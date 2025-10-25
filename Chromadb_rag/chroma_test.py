"""
Test Program: Query Patient's Past Medications
Query a specific patient's past medications from ChromaDB
"""

import chromadb
import os


def query_past_medications(patient_id: str, api_key: str, tenant: str, database: str):
    """
    Query a patient's past medications from ChromaDB
    
    Args:
        patient_id: Patient ID (used as collection name)
        api_key: ChromaDB API key
        tenant: ChromaDB tenant
        database: ChromaDB database name
    """
    
    print("="*60)
    print("QUERY PATIENT'S PAST MEDICATIONS")
    print("="*60)
    print(f"Patient ID: {patient_id}")
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
        print(f"\n💡 Available collections:")
        collections = client.list_collections()
        for col in collections:
            print(f"   - {col.name}")
        return
    
    # Get the past_medications document
    print(f"\n📋 Retrieving past medications document...")
    
    try:
        result = collection.get(ids=["past_medications"])
        
        if result['ids']:
            print("✅ Past medications found!")
            print("\n" + "="*60)
            print("PAST MEDICATIONS")
            print("="*60)
            print(result['documents'][0])
            print("="*60)
            
            # Show metadata
            print("\n📊 Metadata:")
            metadata = result['metadatas'][0]
            print(f"   Document Type: {metadata.get('document_type')}")
            print(f"   Patient ID: {metadata.get('patient_id')}")
            print(f"   Patient Name: {metadata.get('patient_name')}")
            print(f"   Total Medications: {metadata.get('total_medications')}")
            print(f"   Categories: {metadata.get('medication_categories')}")
            print(f"   Last Updated: {metadata.get('last_updated')}")
            
        else:
            print("⚠️  No past medications found for this patient")
            print("   (This document only exists if patient has past medications)")
            
    except Exception as e:
        print(f"❌ Error retrieving document: {e}")
        print(f"\n💡 Available documents in this collection:")
        all_docs = collection.get()
        for doc_id in all_docs['ids']:
            print(f"   - {doc_id}")


def main():
    """Main function"""
    
    # Configuration - UPDATE THESE
    API_KEY = os.environ.get('CHROMADB_API_KEY', 'ck-7y5MiWPpw4faaxXST9MB4ArfZHBHoEiUk72BJ4eJHRJy')
    TENANT = os.environ.get('CHROMADB_TENANT', '02a43515-0e15-440c-999f-b1dc0242aa7d')
    DATABASE = os.environ.get('CHROMADB_DATABASE', 'CalHacks2025')
    
    # Patient ID to query
    PATIENT_ID = '073290f9-73e6-8842-bddc-b568bfcb84b0'  # ← UPDATE THIS IF NEEDED
    
    # Query the patient's past medications
    query_past_medications(
        patient_id=PATIENT_ID,
        api_key=API_KEY,
        tenant=TENANT,
        database=DATABASE
    )


if __name__ == '__main__':
    main()