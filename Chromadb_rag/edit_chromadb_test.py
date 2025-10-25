"""
Edit Patient Document: Update Recent Vitals Weight
Modify the weight in a patient's recent_vitals document
"""

import chromadb
import os
import re


def update_weight_in_vitals(patient_id: str, new_weight_kg: float, 
                           api_key: str, tenant: str, database: str):
    """
    Update the weight value in a patient's recent_vitals document
    
    Args:
        patient_id: Patient ID (collection name)
        new_weight_kg: New weight in kilograms
        api_key: ChromaDB API key
        tenant: ChromaDB tenant
        database: ChromaDB database name
    """
    
    print("="*60)
    print("UPDATE PATIENT'S WEIGHT IN RECENT VITALS")
    print("="*60)
    print(f"Patient ID: {patient_id}")
    print(f"New Weight: {new_weight_kg} kg")
    print(f"Database: {database}")
    print()
    
    # Connect to ChromaDB
    print("🔌 Connecting to ChromaDB Cloud...")
    try:
        client = chromadb.CloudClient(
            api_key=api_key,
            tenant=tenant,
            database=database
        )
        print("✅ Connected successfully!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Get patient's collection
    collection_name = patient_id.replace(':', '-').replace(' ', '_')
    print(f"\n📂 Opening collection: {collection_name}")
    
    try:
        collection = client.get_collection(collection_name)
        print("✅ Collection found!")
    except Exception as e:
        print(f"❌ Collection not found: {e}")
        return
    
    # Get current recent_vitals document
    print(f"\n📋 Retrieving current recent_vitals document...")
    
    try:
        result = collection.get(ids=["recent_vitals"])
        
        if not result['ids']:
            print("❌ recent_vitals document not found")
            return
        
        current_text = result['documents'][0]
        current_metadata = result['metadatas'][0]
        
        print("✅ Document retrieved!")
        print("\n" + "="*60)
        print("CURRENT VITALS (BEFORE UPDATE)")
        print("="*60)
        print(current_text)
        print("="*60)
        
        # Update the weight in the text
        print(f"\n🔧 Updating weight to {new_weight_kg} kg...")
        
        # Pattern to match weight line (e.g., "Body Weight: 73 kg")
        weight_pattern = r'Body Weight:\s*\d+(?:\.\d+)?\s*kg'
        
        # New weight text
        new_weight_text = f"Body Weight: {int(new_weight_kg)} kg"
        
        # Replace weight in text
        updated_text = re.sub(weight_pattern, new_weight_text, current_text)
        
        # Also update BMI if present (need height)
        # Extract current height
        height_match = re.search(r'Body Height:\s*(\d+(?:\.\d+)?)\s*cm', current_text)
        if height_match:
            height_cm = float(height_match.group(1))
            # Calculate new BMI
            height_m = height_cm / 100
            new_bmi = new_weight_kg / (height_m ** 2)
            
            # Update BMI in text
            bmi_pattern = r'Body mass index \(BMI\) \[Ratio\]:\s*\d+(?:\.\d+)?\s*kg/m2'
            new_bmi_text = f"Body mass index (BMI) [Ratio]: {new_bmi:.2f} kg/m2"
            updated_text = re.sub(bmi_pattern, new_bmi_text, updated_text)
            
            # Determine BMI category
            if new_bmi < 18.5:
                bmi_category = 'underweight'
            elif new_bmi < 25:
                bmi_category = 'normal'
            elif new_bmi < 30:
                bmi_category = 'overweight'
            else:
                bmi_category = 'obese'
            
            # Update metadata BMI category
            current_metadata['bmi_category'] = bmi_category
        
        # Update the document in ChromaDB
        print("💾 Saving updated document...")
        
        collection.update(
            ids=["recent_vitals"],
            documents=[updated_text],
            metadatas=[current_metadata]
        )
        
        print("✅ Document updated successfully!")
        
        # Retrieve and display updated document
        print("\n" + "="*60)
        print("UPDATED VITALS (AFTER UPDATE)")
        print("="*60)
        
        result = collection.get(ids=["recent_vitals"])
        print(result['documents'][0])
        print("="*60)
        
        print(f"\n📊 Updated Metadata:")
        metadata = result['metadatas'][0]
        print(f"   BMI Category: {metadata.get('bmi_category')}")
        print(f"   Last Updated: {metadata.get('last_updated')}")
        
        print("\n✅ Weight successfully updated!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    
    # Configuration
    API_KEY = os.environ.get('CHROMADB_API_KEY', 'ck-7y5MiWPpw4faaxXST9MB4ArfZHBHoEiUk72BJ4eJHRJy')
    TENANT = os.environ.get('CHROMADB_TENANT', '02a43515-0e15-440c-999f-b1dc0242aa7d')
    DATABASE = os.environ.get('CHROMADB_DATABASE', 'CalHacks2025')
    
    # Patient ID to update
    PATIENT_ID = '073290f9-73e6-8842-bddc-b568bfcb84b0'
    
    # New weight value
    NEW_WEIGHT_KG = 100  # ← CHANGE THIS VALUE
    
    # Update the weight
    update_weight_in_vitals(
        patient_id=PATIENT_ID,
        new_weight_kg=NEW_WEIGHT_KG,
        api_key=API_KEY,
        tenant=TENANT,
        database=DATABASE
    )


if __name__ == '__main__':
    main()