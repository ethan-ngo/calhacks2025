"""
FHIR JSON to ChromaDB Parser
This script parses FHIR Bundle JSON files and stores patient data in ChromaDB Cloud.
"""
from collections import defaultdict
import json
import chromadb
from datetime import datetime
from typing import Dict, List, Any, Optional
import os


class FHIRToChromaDB:
    """Parser for FHIR JSON files that stores data in ChromaDB Cloud - one collection per patient"""
    
    def __init__(self, api_key: str, tenant: str, database: str):
        """
        Initialize ChromaDB Cloud client
        
        Args:
            api_key: ChromaDB Cloud API key
            tenant: ChromaDB Cloud tenant name
            database: ChromaDB Cloud database name
        """
        self.api_key = api_key
        self.tenant = tenant
        self.database = database
        self.client = None
        self.patient_id = None
        self.patient_name = None
        self.collection = None
        
    def parse_fhir_json(self, json_path: str) -> Dict[str, Any]:
        """
        Parse FHIR JSON file
        
        Args:
            json_path: Path to FHIR JSON file
            
        Returns:
            Parsed FHIR Bundle data
        """
        with open(json_path, 'r') as f:
            return json.load(f)
    
    def extract_patient_info(self, patient_resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract patient information from Patient resource
        
        Args:
            patient_resource: FHIR Patient resource
            
        Returns:
            Extracted patient information
        """
        patient_info = {
            'id': patient_resource.get('id'),
            'resourceType': 'Patient',
        }
        
        # Extract name
        if 'name' in patient_resource and len(patient_resource['name']) > 0:
            name = patient_resource['name'][0]
            patient_info['family_name'] = name.get('family', '')
            patient_info['given_names'] = ' '.join(name.get('given', []))
            patient_info['prefix'] = ' '.join(name.get('prefix', []))
            patient_info['full_name'] = f"{patient_info['prefix']} {patient_info['given_names']} {patient_info['family_name']}".strip()
        
        # Extract gender and birth date
        patient_info['gender'] = patient_resource.get('gender', '')
        patient_info['birth_date'] = patient_resource.get('birthDate', '')
        
        # Extract address
        if 'address' in patient_resource and len(patient_resource['address']) > 0:
            address = patient_resource['address'][0]
            patient_info['address_line'] = ', '.join(address.get('line', []))
            patient_info['city'] = address.get('city', '')
            patient_info['state'] = address.get('state', '')
            patient_info['postal_code'] = address.get('postalCode', '')
            patient_info['country'] = address.get('country', '')
        
        # Extract telecom
        if 'telecom' in patient_resource:
            for telecom in patient_resource['telecom']:
                system = telecom.get('system', '')
                value = telecom.get('value', '')
                if system == 'phone':
                    patient_info['phone'] = value
                elif system == 'email':
                    patient_info['email'] = value
        
        # Extract marital status
        if 'maritalStatus' in patient_resource:
            marital_status = patient_resource['maritalStatus']
            if 'text' in marital_status:
                patient_info['marital_status'] = marital_status['text']
            elif 'coding' in marital_status and len(marital_status['coding']) > 0:
                patient_info['marital_status'] = marital_status['coding'][0].get('display', '')
        
        # Extract multiple birth indicator
        if 'multipleBirthBoolean' in patient_resource:
            patient_info['multiple_birth'] = patient_resource['multipleBirthBoolean']
        
        # Extract race and ethnicity from extensions
        if 'extension' in patient_resource:
            for ext in patient_resource['extension']:
                url = ext.get('url', '')
                if 'us-core-race' in url:
                    for sub_ext in ext.get('extension', []):
                        if sub_ext.get('url') == 'text':
                            patient_info['race'] = sub_ext.get('valueString', '')
                elif 'us-core-ethnicity' in url:
                    for sub_ext in ext.get('extension', []):
                        if sub_ext.get('url') == 'text':
                            patient_info['ethnicity'] = sub_ext.get('valueString', '')
        
        return patient_info
    
    def extract_encounter_info(self, encounter_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Extract information from Encounter resource"""
        encounter_info = {
            'id': encounter_resource.get('id'),
            'resourceType': 'Encounter',
            'status': encounter_resource.get('status', ''),
            'class': encounter_resource.get('class', {}).get('code', ''),
        }
        
        # Extract type
        if 'type' in encounter_resource and len(encounter_resource['type']) > 0:
            type_coding = encounter_resource['type'][0].get('coding', [{}])[0]
            encounter_info['type_code'] = type_coding.get('code', '')
            encounter_info['type_display'] = type_coding.get('display', '')
        
        # Extract period
        if 'period' in encounter_resource:
            period = encounter_resource['period']
            encounter_info['start'] = period.get('start', '')
            encounter_info['end'] = period.get('end', '')
        
        # Extract service provider
        if 'serviceProvider' in encounter_resource:
            encounter_info['service_provider'] = encounter_resource['serviceProvider'].get('display', '')
        
        return encounter_info
    
    def extract_condition_info(self, condition_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Extract information from Condition resource"""
        condition_info = {
            'id': condition_resource.get('id'),
            'resourceType': 'Condition',
            'clinical_status': condition_resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', ''),
        }
        
        # Extract code (diagnosis)
        if 'code' in condition_resource:
            code = condition_resource['code']
            if 'coding' in code and len(code['coding']) > 0:
                coding = code['coding'][0]
                condition_info['code'] = coding.get('code', '')
                condition_info['display'] = coding.get('display', '')
                condition_info['system'] = coding.get('system', '')
            if 'text' in code:
                condition_info['text'] = code['text']
        
        # Extract onset date
        if 'onsetDateTime' in condition_resource:
            condition_info['onset_date'] = condition_resource['onsetDateTime']
        
        # Extract recorded date
        if 'recordedDate' in condition_resource:
            condition_info['recorded_date'] = condition_resource['recordedDate']
        
        return condition_info
    
    def extract_observation_info(self, observation_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Extract information from Observation resource"""
        observation_info = {
            'id': observation_resource.get('id'),
            'resourceType': 'Observation',
            'status': observation_resource.get('status', ''),
        }
        
        # Extract category
        if 'category' in observation_resource and len(observation_resource['category']) > 0:
            category = observation_resource['category'][0].get('coding', [{}])[0]
            observation_info['category_code'] = category.get('code', '')
            observation_info['category_display'] = category.get('display', '')
        
        # Extract code (what was observed)
        if 'code' in observation_resource:
            code = observation_resource['code']
            if 'coding' in code and len(code['coding']) > 0:
                coding = code['coding'][0]
                observation_info['code'] = coding.get('code', '')
                observation_info['display'] = coding.get('display', '')
            if 'text' in code:
                observation_info['text'] = code['text']
        
        # Extract effective date/time
        if 'effectiveDateTime' in observation_resource:
            observation_info['effective_date'] = observation_resource['effectiveDateTime']
        
        # Extract value
        if 'valueQuantity' in observation_resource:
            value = observation_resource['valueQuantity']
            observation_info['value'] = value.get('value', '')
            observation_info['unit'] = value.get('unit', '')
            observation_info['value_string'] = f"{value.get('value', '')} {value.get('unit', '')}"
        elif 'valueCodeableConcept' in observation_resource:
            value_concept = observation_resource['valueCodeableConcept']
            if 'coding' in value_concept and len(value_concept['coding']) > 0:
                observation_info['value_code'] = value_concept['coding'][0].get('code', '')
                observation_info['value_display'] = value_concept['coding'][0].get('display', '')
            if 'text' in value_concept:
                observation_info['value_string'] = value_concept['text']
        elif 'valueString' in observation_resource:
            observation_info['value_string'] = observation_resource['valueString']
        
        return observation_info
    
    def extract_diagnostic_report_info(self, report_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Extract information from DiagnosticReport resource"""
        report_info = {
            'id': report_resource.get('id'),
            'resourceType': 'DiagnosticReport',
            'status': report_resource.get('status', ''),
        }
        
        # Extract category
        if 'category' in report_resource and len(report_resource['category']) > 0:
            category = report_resource['category'][0].get('coding', [{}])[0]
            report_info['category_code'] = category.get('code', '')
            report_info['category_display'] = category.get('display', '')
        
        # Extract code
        if 'code' in report_resource:
            code = report_resource['code']
            if 'coding' in code and len(code['coding']) > 0:
                coding = code['coding'][0]
                report_info['code'] = coding.get('code', '')
                report_info['display'] = coding.get('display', '')
        
        # Extract effective date
        if 'effectiveDateTime' in report_resource:
            report_info['effective_date'] = report_resource['effectiveDateTime']
        
        # Extract issued date
        if 'issued' in report_resource:
            report_info['issued_date'] = report_resource['issued']
        
        return report_info
    
    def extract_claim_info(self, claim_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Extract information from Claim resource"""
        claim_info = {
            'id': claim_resource.get('id'),
            'resourceType': 'Claim',
            'status': claim_resource.get('status', ''),
            'use': claim_resource.get('use', ''),
        }
        
        # Extract type
        if 'type' in claim_resource:
            type_coding = claim_resource['type'].get('coding', [{}])[0]
            claim_info['type_code'] = type_coding.get('code', '')
            claim_info['type_display'] = type_coding.get('display', '')
        
        # Extract created date
        if 'created' in claim_resource:
            claim_info['created_date'] = claim_resource['created']
        
        # Extract total
        if 'total' in claim_resource:
            total = claim_resource['total']
            claim_info['total_value'] = total.get('value', '')
            claim_info['total_currency'] = total.get('currency', '')
            claim_info['total_string'] = f"{total.get('currency', '')} {total.get('value', '')}"
        
        return claim_info
    
    def extract_explanation_of_benefit_info(self, eob_resource: Dict[str, Any]) -> Dict[str, Any]:
        """Extract information from ExplanationOfBenefit resource"""
        eob_info = {
            'id': eob_resource.get('id'),
            'resourceType': 'ExplanationOfBenefit',
            'status': eob_resource.get('status', ''),
            'use': eob_resource.get('use', ''),
        }
        
        # Extract type
        if 'type' in eob_resource:
            type_coding = eob_resource['type'].get('coding', [{}])[0]
            eob_info['type_code'] = type_coding.get('code', '')
            eob_info['type_display'] = type_coding.get('display', '')
        
        # Extract created date
        if 'created' in eob_resource:
            eob_info['created_date'] = eob_resource['created']
        
        # Extract outcome
        if 'outcome' in eob_resource:
            eob_info['outcome'] = eob_resource['outcome']
        
        # Extract total
        if 'total' in eob_resource:
            for total in eob_resource['total']:
                category = total.get('category', {}).get('coding', [{}])[0].get('code', '')
                amount = total.get('amount', {})
                eob_info[f'{category}_value'] = amount.get('value', '')
                eob_info[f'{category}_currency'] = amount.get('currency', '')
        
        # Extract payment
        if 'payment' in eob_resource:
            payment = eob_resource['payment']
            if 'amount' in payment:
                amount = payment['amount']
                eob_info['payment_value'] = amount.get('value', '')
                eob_info['payment_currency'] = amount.get('currency', '')
        
        return eob_info
    
    def create_document_text(self, resource_info: Dict[str, Any]) -> str:
        """
        Create a text document from resource info for embedding
        
        Args:
            resource_info: Extracted resource information
            
        Returns:
            Text representation of the resource
        """
        resource_type = resource_info.get('resourceType', 'Unknown')
        text_parts = [f"Resource Type: {resource_type}"]
        
        # Add all key-value pairs as text
        for key, value in resource_info.items():
            if key != 'resourceType' and value:
                # Convert key from snake_case to readable format
                readable_key = key.replace('_', ' ').title()
                text_parts.append(f"{readable_key}: {value}")
        
        return "\n".join(text_parts)
    
    def process_fhir_bundle(self, json_path: str):
        """
        Process FHIR Bundle and store in ChromaDB as organized documents
        
        Args:
            json_path: Path to FHIR JSON file
        """
        # Parse JSON
        print(f"Parsing FHIR JSON file: {json_path}")
        bundle_data = self.parse_fhir_json(json_path)
        
        if bundle_data.get('resourceType') != 'Bundle':
            raise ValueError("JSON file is not a FHIR Bundle")
        
        entries = bundle_data.get('entry', [])
        print(f"Found {len(entries)} entries in the bundle")
        
        # Extract patient ID
        patient_entry = next((e for e in entries if e['resource']['resourceType'] == 'Patient'), None)
        if not patient_entry:
            raise ValueError("No Patient resource found in bundle")
        
        self.patient_id = patient_entry['resource']['id']
        patient_info = self.extract_patient_info(patient_entry['resource'])
        self.patient_name = patient_info.get('full_name', 'Unknown Patient')
        
        print(f"\nPatient ID: {self.patient_id}")
        print(f"Patient Name: {self.patient_name}")
        
        # Connect to the database
        print(f"\nConnecting to ChromaDB Cloud database: {self.database}")
        try:
            self.client = chromadb.CloudClient(
                api_key=self.api_key,
                tenant=self.tenant,
                database=self.database
            )
            print(f"✓ Successfully connected to database: {self.database}")
            
        except Exception as e:
            print(f"Error connecting to ChromaDB Cloud: {e}")
            raise
        
        # Create patient-specific collection
        collection_name = self.patient_id.replace(':', '-').replace(' ', '_')
        print(f"\nCreating patient collection: {collection_name}")
        
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "patient_id": self.patient_id,
                    "patient_name": self.patient_name,
                    "date_of_birth": patient_info.get('birth_date', ''),
                    "age": patient_info.get('age', 0),
                    "gender": patient_info.get('gender', ''),
                    "last_updated": datetime.now().isoformat()[:10]
                }
            )
            print(f"✓ Collection created: {collection_name}")
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise
        
        # Process all resources by type
        resources_by_type = defaultdict(list)
        for entry in entries:
            resource = entry.get('resource', {})
            resource_type = resource.get('resourceType')
            if resource_type:
                resources_by_type[resource_type].append(resource)
        
        print(f"\nProcessing medical records...")
        
        # Create documents
        documents = []
        metadatas = []
        ids = []
        
        # 1. Patient Information (always created)
        doc_text, doc_meta = self._create_patient_information_doc(patient_info)
        documents.append(doc_text)
        metadatas.append(doc_meta)
        ids.append("patient_information")
        print("  ✓ Created: patient_information")
        
        # 2. Active Conditions
        doc_text, doc_meta = self._create_active_conditions_doc(resources_by_type.get('Condition', []))
        documents.append(doc_text)
        metadatas.append(doc_meta)
        ids.append("active_conditions")
        print("  ✓ Created: active_conditions")
        
        # 3. Past Conditions
        doc_text, doc_meta = self._create_past_conditions_doc(resources_by_type.get('Condition', []))
        documents.append(doc_text)
        metadatas.append(doc_meta)
        ids.append("past_conditions")
        print("  ✓ Created: past_conditions")
        
        # 4. Current Medications (only if exists)
        current_meds = self._get_current_medications(
            resources_by_type.get('Medication', []),
            resources_by_type.get('MedicationRequest', [])
        )
        if current_meds:
            doc_text, doc_meta = self._create_current_medications_doc(current_meds)
            documents.append(doc_text)
            metadatas.append(doc_meta)
            ids.append("current_medications")
            print("  ✓ Created: current_medications")
        
        # 5. Past Medications (only if exists)
        past_meds = self._get_past_medications(resources_by_type.get('MedicationRequest', []))
        if past_meds:
            doc_text, doc_meta = self._create_past_medications_doc(past_meds)
            documents.append(doc_text)
            metadatas.append(doc_meta)
            ids.append("past_medications")
            print("  ✓ Created: past_medications")
        
        # 6. Recent Vitals
        vitals = self._get_vital_signs(resources_by_type.get('Observation', []))
        if vitals:
            doc_text, doc_meta = self._create_vitals_doc(vitals)
            documents.append(doc_text)
            metadatas.append(doc_meta)
            ids.append("recent_vitals")
            print("  ✓ Created: recent_vitals")
        
        # 7. Recent Labs (only if exists)
        labs = self._get_lab_results(resources_by_type.get('Observation', []))
        if labs:
            doc_text, doc_meta = self._create_labs_doc(labs)
            documents.append(doc_text)
            metadatas.append(doc_meta)
            ids.append("recent_labs")
            print("  ✓ Created: recent_labs")
        
        # 8. Immunizations
        immunizations = resources_by_type.get('Immunization', [])
        if immunizations:
            doc_text, doc_meta = self._create_immunizations_doc(immunizations)
            documents.append(doc_text)
            metadatas.append(doc_meta)
            ids.append("immunizations")
            print("  ✓ Created: immunizations")
        
        # 9. Procedures (ALL procedures)
        procedures = resources_by_type.get('Procedure', [])
        if procedures:
            doc_text, doc_meta = self._create_procedures_doc(procedures)
            documents.append(doc_text)
            metadatas.append(doc_meta)
            ids.append("procedures")
            print("  ✓ Created: procedures")
        
        # 10. Allergies (only if exists)
        allergies = resources_by_type.get('AllergyIntolerance', [])
        if allergies:
            doc_text, doc_meta = self._create_allergies_doc(allergies)
            documents.append(doc_text)
            metadatas.append(doc_meta)
            ids.append("allergies")
            print("  ✓ Created: allergies")
        
        # 11. Family History (only if exists)
        family_history = resources_by_type.get('FamilyMemberHistory', [])
        if family_history:
            doc_text, doc_meta = self._create_family_history_doc(family_history)
            documents.append(doc_text)
            metadatas.append(doc_meta)
            ids.append("family_history")
            print("  ✓ Created: family_history")
        
        # 12. Social History (only if exists)
        social_obs = self._get_social_history(resources_by_type.get('Observation', []))
        if social_obs:
            doc_text, doc_meta = self._create_social_history_doc(social_obs, resources_by_type.get('Condition', []))
            documents.append(doc_text)
            metadatas.append(doc_meta)
            ids.append("social_history")
            print("  ✓ Created: social_history")
        
        # Add all documents to collection
        print(f"\nUploading {len(documents)} documents to ChromaDB...")
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✓ Successfully uploaded {len(documents)} documents")
        except Exception as e:
            print(f"Error uploading documents: {e}")
            raise
        
        print(f"\n{'='*60}")
        print("PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Collection Name: {collection_name}")
        print(f"Patient ID: {self.patient_id}")
        print(f"Patient Name: {self.patient_name}")
        print(f"Total Documents: {len(documents)}")
        print(f"{'='*60}\n")
        
        return {
            'collection_name': collection_name,
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'total_documents': len(documents),
            'document_types': ids
        }
    
    # Helper methods for creating documents
    
    def _create_patient_information_doc(self, patient_info: Dict[str, Any]) -> tuple:
        """Create patient information document"""
        text = f"""PATIENT INFORMATION

Name: {patient_info.get('full_name', 'Unknown')}
Patient ID: {patient_info.get('id', 'Unknown')}
Date of Birth: {patient_info.get('birth_date', 'Unknown')}
Age: {patient_info.get('age', 'Unknown')} years old
Gender: {patient_info.get('gender', 'Unknown').capitalize()}
Race: {patient_info.get('race', 'Not documented')}
Ethnicity: {patient_info.get('ethnicity', 'Not documented')}
Marital Status: {patient_info.get('marital_status', 'Not documented')}

CONTACT INFORMATION:
Address: {patient_info.get('full_address', 'Not documented')}
Phone: {patient_info.get('phone', 'Not documented')}
"""
        
        metadata = {
            'document_type': 'patient_information',
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'age': patient_info.get('age', 0),
            'gender': patient_info.get('gender', ''),
            'last_updated': datetime.now().isoformat()[:10]
        }
        
        return text, metadata
    
    def _create_active_conditions_doc(self, conditions: List[Dict]) -> tuple:
        """Create active conditions document"""
        active = [c for c in conditions if c.get('clinicalStatus', {}).get('coding', [{}])[0].get('code') == 'active']
        
        text = f"ACTIVE MEDICAL CONDITIONS ({len(active)}):\n\n"
        
        chronic_conditions = []
        has_alerts = False
        alert_types = []
        
        for i, cond in enumerate(active, 1):
            name = 'Unknown Condition'
            code = ''
            
            if 'code' in cond:
                if 'text' in cond['code']:
                    name = cond['code']['text']
                elif 'coding' in cond['code'] and len(cond['code']['coding']) > 0:
                    name = cond['code']['coding'][0].get('display', 'Unknown')
                    code = cond['code']['coding'][0].get('code', '')
            
            onset = cond.get('onsetDateTime', cond.get('recordedDate', 'Unknown'))[:10]
            
            text += f"{i}. {name}\n"
            if code:
                text += f"   Code: {code}\n"
            text += f"   Onset Date: {onset}\n"
            text += f"   Status: Active\n"
            
            # Check for chronic conditions
            if 'chronic' in name.lower():
                chronic_conditions.append(name)
            
            # Check for alerts
            if 'abuse' in name.lower() or 'violence' in name.lower():
                has_alerts = True
                alert_types.append('intimate_partner_abuse')
                text += f"   ⚠️ ALERT: Requires follow-up and support services\n"
            
            text += "\n"
        
        if not active:
            text += "No active conditions documented.\n"
        
        metadata = {
            'document_type': 'active_conditions',
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'total_conditions': len(active),
            'chronic_conditions': ', '.join(chronic_conditions) if chronic_conditions else '',
            'has_alerts': has_alerts,
            'alert_types': ', '.join(alert_types) if alert_types else '',
            'last_updated': datetime.now().isoformat()[:10]
        }
        
        return text, metadata
    
    def _create_past_conditions_doc(self, conditions: List[Dict]) -> tuple:
        """Create past/resolved conditions document"""
        past = [c for c in conditions if c.get('clinicalStatus', {}).get('coding', [{}])[0].get('code') != 'active']
        
        text = f"RESOLVED/PAST MEDICAL CONDITIONS ({len(past)}):\n\n"
        
        notable_history = []
        
        for i, cond in enumerate(past, 1):
            name = 'Unknown Condition'
            code = ''
            
            if 'code' in cond:
                if 'text' in cond['code']:
                    name = cond['code']['text']
                elif 'coding' in cond['code'] and len(cond['code']['coding']) > 0:
                    name = cond['code']['coding'][0].get('display', 'Unknown')
                    code = cond['code']['coding'][0].get('code', '')
            
            onset = cond.get('onsetDateTime', cond.get('recordedDate', 'Unknown'))[:10]
            
            text += f"{i}. {name}\n"
            if code:
                text += f"   Code: {code}\n"
            text += f"   Date: {onset}\n"
            text += f"   Status: Resolved\n\n"
            
            # Track notable history
            if any(keyword in name.lower() for keyword in ['miscarriage', 'anemia', 'substance', 'alcohol', 'cancer']):
                notable_history.append(name.lower().split()[0])
        
        if not past:
            text += "No past conditions documented.\n"
        
        metadata = {
            'document_type': 'past_conditions',
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'total_conditions': len(past),
            'notable_history': ', '.join(list(set(notable_history))) if notable_history else '',
            'last_updated': datetime.now().isoformat()[:10]
        }
        
        return text, metadata
    
    def _get_current_medications(self, medications: List[Dict], medication_requests: List[Dict]) -> List[Dict]:
        """Get current medications from Medication and MedicationRequest resources"""
        current = []
        
        # Add from Medication resources
        for med in medications:
            current.append({
                'name': self._get_codeable_concept_text(med.get('code', {})),
                'code': self._get_codeable_concept_code(med.get('code', {})),
                'type': 'current',
                'id': med.get('id')
            })
        
        # Add recent/active from MedicationRequest
        for req in medication_requests:
            status = req.get('status', '')
            if status in ['active', 'completed']:
                authored = req.get('authoredOn', '')
                # Consider recent if within last 2 years or no date
                if not authored or authored[:4] >= '2023':
                    current.append({
                        'name': self._get_codeable_concept_text(req.get('medicationCodeableConcept', {})),
                        'code': self._get_codeable_concept_code(req.get('medicationCodeableConcept', {})),
                        'type': 'prescription',
                        'status': status,
                        'date': authored[:10] if authored else '',
                        'dosage': req.get('dosageInstruction', [{}])[0].get('text', '') if req.get('dosageInstruction') else '',
                        'id': req.get('id')
                    })
        
        return current
    
    def _get_past_medications(self, medication_requests: List[Dict]) -> List[Dict]:
        """Get past medications from MedicationRequest resources"""
        past = []
        
        for req in medication_requests:
            status = req.get('status', '')
            authored = req.get('authoredOn', '')
            
            # Consider past if old or completed
            if authored and authored[:4] < '2023':
                past.append({
                    'name': self._get_codeable_concept_text(req.get('medicationCodeableConcept', {})),
                    'code': self._get_codeable_concept_code(req.get('medicationCodeableConcept', {})),
                    'date': authored[:10],
                    'status': status,
                    'id': req.get('id')
                })
        
        return past
    
    def _create_current_medications_doc(self, medications: List[Dict]) -> tuple:
        """Create current medications document"""
        text = f"CURRENT MEDICATIONS ({len(medications)}):\n\n"
        
        has_controlled = False
        controlled_list = []
        has_contraceptive = False
        
        for i, med in enumerate(medications, 1):
            name = med.get('name', 'Unknown Medication')
            code = med.get('code', '')
            
            text += f"{i}. {name}\n"
            if code:
                text += f"   Code: {code}\n"
            if 'dosage' in med and med['dosage']:
                text += f"   Dosage: {med['dosage']}\n"
            if 'date' in med and med['date']:
                text += f"   Started: {med['date']}\n"
            
            # Check for controlled substances
            if any(drug in name.lower() for drug in ['tramadol', 'oxycodone', 'hydrocodone', 'morphine', 'fentanyl']):
                has_controlled = True
                controlled_list.append(name.split()[0])
                text += f"   ⚠️ NOTE: Controlled substance - monitor for tolerance/dependence\n"
            
            # Check for contraceptives
            if any(term in name.lower() for term in ['contraceptive', 'birth control', 'iud', 'mirena', 'levora', 'nuvaring']):
                has_contraceptive = True
                text += f"   Purpose: Contraception\n"
            
            text += "\n"
        
        metadata = {
            'document_type': 'current_medications',
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'total_medications': len(medications),
            'has_controlled_substances': has_controlled,
            'controlled_substances': ', '.join(controlled_list) if controlled_list else '',
            'contraceptive_use': has_contraceptive,
            'last_updated': datetime.now().isoformat()[:10]
        }
        
        return text, metadata
    
    def _create_past_medications_doc(self, medications: List[Dict]) -> tuple:
        """Create past medications document"""
        text = f"PAST MEDICATIONS ({len(medications)}):\n\n"
        
        categories = []
        
        for i, med in enumerate(medications, 1):
            name = med.get('name', 'Unknown Medication')
            date = med.get('date', 'Unknown')
            status = med.get('status', '')
            
            text += f"{i}. {name}\n"
            text += f"   Prescribed: {date}\n"
            text += f"   Status: {status.capitalize()}\n\n"
            
            # Categorize
            if 'contraceptive' in name.lower() or any(term in name.lower() for term in ['levora', 'nuvaring', 'natazia']):
                categories.append('contraceptive')
        
        metadata = {
            'document_type': 'past_medications',
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'total_medications': len(medications),
            'medication_categories': ', '.join(list(set(categories))) if categories else '',
            'last_updated': datetime.now().isoformat()[:10]
        }
        
        return text, metadata
    
    def _get_vital_signs(self, observations: List[Dict]) -> List[Dict]:
        """Get vital sign observations"""
        vitals = []
        
        for obs in observations:
            # Check if it's a vital sign
            is_vital = False
            if 'category' in obs:
                for cat in obs['category']:
                    if 'coding' in cat:
                        for coding in cat['coding']:
                            if 'vital' in coding.get('code', '').lower():
                                is_vital = True
                                break
            
            if is_vital:
                name = self._get_codeable_concept_text(obs.get('code', {}))
                value_str = ''
                
                if 'valueQuantity' in obs:
                    val = obs['valueQuantity']
                    value_str = f"{val.get('value', '')} {val.get('unit', '')}"
                elif 'valueCodeableConcept' in obs:
                    value_str = self._get_codeable_concept_text(obs['valueCodeableConcept'])
                
                vitals.append({
                    'name': name,
                    'value': value_str,
                    'date': obs.get('effectiveDateTime', obs.get('issued', ''))[:10],
                    'id': obs.get('id')
                })
        
        return vitals
    
    def _create_vitals_doc(self, vitals: List[Dict]) -> tuple:
        """Create vitals document with most recent values"""
        # Get most recent for each vital type
        latest_vitals = {}
        for vital in vitals:
            name = vital['name']
            date = vital['date']
            if name not in latest_vitals or date > latest_vitals[name]['date']:
                latest_vitals[name] = vital
        
        # Get the most recent date
        most_recent_date = max([v['date'] for v in latest_vitals.values()]) if latest_vitals else 'Unknown'
        
        text = f"MOST RECENT VITAL SIGNS ({most_recent_date}):\n\n"
        
        bmi_category = 'normal'
        pain_level = 0
        
        for name, vital in sorted(latest_vitals.items()):
            text += f"{name}: {vital['value']}\n"
            
            # Track BMI category
            if 'bmi' in name.lower() and vital['value']:
                try:
                    bmi_val = float(vital['value'].split()[0])
                    if bmi_val >= 30:
                        bmi_category = 'obese'
                    elif bmi_val >= 25:
                        bmi_category = 'overweight'
                    elif bmi_val < 18.5:
                        bmi_category = 'underweight'
                except:
                    pass
            
            # Track pain
            if 'pain' in name.lower() and vital['value']:
                try:
                    pain_level = int(vital['value'].split()[0])
                except:
                    pass
        
        metadata = {
            'document_type': 'recent_vitals',
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'last_measurement_date': most_recent_date,
            'bmi_category': bmi_category,
            'chronic_pain_present': pain_level > 0,
            'pain_level': pain_level,
            'last_updated': datetime.now().isoformat()[:10]
        }
        
        return text, metadata
    
    def _get_lab_results(self, observations: List[Dict]) -> List[Dict]:
        """Get laboratory observations"""
        labs = []
        
        for obs in observations:
            # Check if it's a lab result
            is_lab = False
            if 'category' in obs:
                for cat in obs['category']:
                    if 'coding' in cat:
                        for coding in cat['coding']:
                            if 'lab' in coding.get('code', '').lower():
                                is_lab = True
                                break
            
            if is_lab:
                name = self._get_codeable_concept_text(obs.get('code', {}))
                value_str = ''
                
                if 'valueQuantity' in obs:
                    val = obs['valueQuantity']
                    value_str = f"{val.get('value', '')} {val.get('unit', '')}"
                
                labs.append({
                    'name': name,
                    'value': value_str,
                    'date': obs.get('effectiveDateTime', obs.get('issued', ''))[:10],
                    'id': obs.get('id')
                })
        
        return labs
    
    def _create_labs_doc(self, labs: List[Dict]) -> tuple:
        """Create labs document"""
        # Group by date
        labs_by_date = {}
        for lab in labs:
            date = lab['date']
            if date not in labs_by_date:
                labs_by_date[date] = []
            labs_by_date[date].append(lab)
        
        text = "RECENT LABORATORY RESULTS:\n\n"
        
        # Show most recent dates first
        for date in sorted(labs_by_date.keys(), reverse=True)[:5]:  # Last 5 test dates
            text += f"=== {date} ===\n"
            for lab in labs_by_date[date]:
                text += f"{lab['name']}: {lab['value']}\n"
            text += "\n"
        
        most_recent_date = max(labs_by_date.keys()) if labs_by_date else 'Unknown'
        
        metadata = {
            'document_type': 'recent_labs',
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'last_lab_date': most_recent_date,
            'total_lab_results': len(labs),
            'last_updated': datetime.now().isoformat()[:10]
        }
        
        return text, metadata
    
    def _create_immunizations_doc(self, immunizations: List[Dict]) -> tuple:
        """Create immunizations document"""
        # Sort by date
        imm_sorted = sorted(immunizations, key=lambda x: x.get('occurrenceDateTime', ''), reverse=True)
        
        text = f"IMMUNIZATION HISTORY ({len(immunizations)} Total):\n\n"
        
        # Group by vaccine type
        vaccines = {}
        for imm in imm_sorted:
            name = self._get_codeable_concept_text(imm.get('vaccineCode', {}))
            date = imm.get('occurrenceDateTime', '')[:10]
            status = imm.get('status', '')
            
            if name not in vaccines:
                vaccines[name] = []
            vaccines[name].append({'date': date, 'status': status})
        
        # Show vaccines with most recent first
        for vaccine_name in sorted(vaccines.keys()):
            dates = vaccines[vaccine_name]
            text += f"✓ {vaccine_name}\n"
            text += f"   Most Recent: {dates[0]['date']}\n"
            if len(dates) > 1:
                text += f"   Total Doses: {len(dates)}\n"
            text += f"   Status: {dates[0]['status'].capitalize()}\n\n"
        
        last_vaccination = imm_sorted[0].get('occurrenceDateTime', '')[:10] if imm_sorted else 'Unknown'
        
        metadata = {
            'document_type': 'immunizations',
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'total_immunizations': len(immunizations),
            'unique_vaccines': len(vaccines),
            'last_vaccination_date': last_vaccination,
            'last_updated': datetime.now().isoformat()[:10]
        }
        
        return text, metadata
    
    def _create_procedures_doc(self, procedures: List[Dict]) -> tuple:
        """Create procedures document - ALL procedures included"""
        # Sort by date
        proc_sorted = sorted(procedures, 
                           key=lambda x: x.get('performedPeriod', {}).get('start', 
                                        x.get('performedDateTime', ''))[:10], 
                           reverse=True)
        
        text = f"SURGICAL & MEDICAL PROCEDURE HISTORY ({len(procedures)} Total):\n\n"
        
        # Categorize procedures
        surgical = []
        dental = []
        screening = []
        other = []
        
        for proc in proc_sorted:
            name = self._get_codeable_concept_text(proc.get('code', {}))
            date = ''
            if 'performedPeriod' in proc:
                date = proc['performedPeriod'].get('start', '')[:10]
            elif 'performedDateTime' in proc:
                date = proc['performedDateTime'][:10]
            status = proc.get('status', '')
            
            proc_data = {'name': name, 'date': date, 'status': status}
            
            # Categorize
            if any(term in name.lower() for term in ['dental', 'gingivae', 'plaque', 'fluoride']):
                dental.append(proc_data)
            elif any(term in name.lower() for term in ['insertion', 'removal', 'surgery', 'ultrasound', 'iud']):
                surgical.append(proc_data)
            elif any(term in name.lower() for term in ['screening', 'assessment', 'depression', 'anxiety', 'abuse']):
                screening.append(proc_data)
            else:
                other.append(proc_data)
        
        # Show surgical/significant first
        if surgical:
            text += "=== SURGICAL & SIGNIFICANT PROCEDURES ===\n"
            for p in surgical:
                text += f"- {p['name']} ({p['date']})\n"
            text += "\n"
        
        if dental:
            text += "=== DENTAL PROCEDURES ===\n"
            for p in dental[:5]:  # Show recent 5
                text += f"- {p['name']} ({p['date']})\n"
            if len(dental) > 5:
                text += f"  ... and {len(dental) - 5} more dental procedures\n"
            text += "\n"
        
        if screening:
            text += "=== SCREENING & ASSESSMENT PROCEDURES ===\n"
            for p in screening[:10]:  # Show recent 10
                text += f"- {p['name']} ({p['date']})\n"
            if len(screening) > 10:
                text += f"  ... and {len(screening) - 10} more screenings\n"
            text += "\n"
        
        last_procedure_date = proc_sorted[0].get('performedPeriod', {}).get('start', 
                                    proc_sorted[0].get('performedDateTime', ''))[:10] if proc_sorted else 'Unknown'
        
        metadata = {
            'document_type': 'procedures',
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'total_procedures': len(procedures),
            'surgical_procedures': len(surgical),
            'dental_procedures': len(dental),
            'screening_procedures': len(screening),
            'last_procedure_date': last_procedure_date,
            'last_updated': datetime.now().isoformat()[:10]
        }
        
        return text, metadata
    
    def _create_allergies_doc(self, allergies: List[Dict]) -> tuple:
        """Create allergies document"""
        text = f"ALLERGIES ({len(allergies)}):\n\n"
        
        for i, allergy in enumerate(allergies, 1):
            substance = self._get_codeable_concept_text(allergy.get('code', {}))
            reaction = allergy.get('reaction', [{}])[0].get('manifestation', [{}])[0] if allergy.get('reaction') else {}
            reaction_text = self._get_codeable_concept_text(reaction)
            severity = allergy.get('criticality', 'Unknown')
            
            text += f"{i}. {substance}\n"
            if reaction_text:
                text += f"   Reaction: {reaction_text}\n"
            text += f"   Severity: {severity.capitalize()}\n\n"
        
        metadata = {
            'document_type': 'allergies',
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'has_allergies': True,
            'total_allergies': len(allergies),
            'last_updated': datetime.now().isoformat()[:10]
        }
        
        return text, metadata
    
    def _create_family_history_doc(self, family_history: List[Dict]) -> tuple:
        """Create family history document"""
        text = f"FAMILY MEDICAL HISTORY ({len(family_history)} entries):\n\n"
        
        for i, fh in enumerate(family_history, 1):
            relationship = self._get_codeable_concept_text(fh.get('relationship', {}))
            condition = fh.get('condition', [{}])[0] if fh.get('condition') else {}
            condition_name = self._get_codeable_concept_text(condition.get('code', {}))
            
            text += f"{i}. {relationship}: {condition_name}\n"
            if 'onsetAge' in condition:
                text += f"   Onset Age: {condition['onsetAge'].get('value', 'Unknown')}\n"
            text += "\n"
        
        metadata = {
            'document_type': 'family_history',
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'has_family_history': True,
            'total_entries': len(family_history),
            'last_updated': datetime.now().isoformat()[:10]
        }
        
        return text, metadata
    
    def _get_social_history(self, observations: List[Dict]) -> List[Dict]:
        """Get social history observations"""
        social = []
        
        for obs in observations:
            # Check if it's social history
            is_social = False
            if 'category' in obs:
                for cat in obs['category']:
                    if 'coding' in cat:
                        for coding in cat['coding']:
                            if 'social' in coding.get('code', '').lower():
                                is_social = True
                                break
            
            if is_social:
                name = self._get_codeable_concept_text(obs.get('code', {}))
                value_str = ''
                
                if 'valueCodeableConcept' in obs:
                    value_str = self._get_codeable_concept_text(obs['valueCodeableConcept'])
                elif 'valueString' in obs:
                    value_str = obs['valueString']
                
                social.append({
                    'name': name,
                    'value': value_str,
                    'date': obs.get('effectiveDateTime', obs.get('issued', ''))[:10],
                    'id': obs.get('id')
                })
        
        return social
    
    def _create_social_history_doc(self, social_obs: List[Dict], conditions: List[Dict]) -> tuple:
        """Create social history document"""
        text = "SOCIAL & LIFESTYLE HISTORY:\n\n"
        
        tobacco_use = False
        alcohol_history = False
        employed = False
        domestic_violence = False
        
        # Check conditions for social factors
        for cond in conditions:
            name = self._get_codeable_concept_text(cond.get('code', {}))
            if 'alcohol' in name.lower():
                alcohol_history = True
                text += f"=== SUBSTANCE USE ===\n"
                text += f"Alcohol: {name} ({cond.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', '').capitalize()})\n\n"
            if 'abuse' in name.lower() or 'violence' in name.lower():
                domestic_violence = True
                text += f"⚠️ CRITICAL ALERT: {name}\n"
                text += f"   Status: {cond.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', '').capitalize()}\n"
                text += f"   Requires: Safety assessment, counseling referral, social services support\n\n"
            if 'employment' in name.lower():
                employed = True
                text += f"=== EMPLOYMENT ===\n"
                text += f"{name}\n\n"
        
        # Add social observations
        if social_obs:
            text += "=== SOCIAL FACTORS ===\n"
            for obs in social_obs:
                text += f"{obs['name']}: {obs['value']}\n"
            text += "\n"
        
        metadata = {
            'document_type': 'social_history',
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'tobacco_use': tobacco_use,
            'alcohol_history': alcohol_history,
            'employed': employed,
            'domestic_violence_risk': domestic_violence,
            'requires_social_services': domestic_violence,
            'last_updated': datetime.now().isoformat()[:10]
        }
        
        return text, metadata
    
    def _get_codeable_concept_text(self, codeable_concept: Dict) -> str:
        """Helper to extract text from CodeableConcept"""
        if not codeable_concept:
            return ''
        
        if 'text' in codeable_concept:
            return codeable_concept['text']
        elif 'coding' in codeable_concept and len(codeable_concept['coding']) > 0:
            return codeable_concept['coding'][0].get('display', '')
        
        return ''
    
    def _get_codeable_concept_code(self, codeable_concept: Dict) -> str:
        """Helper to extract code from CodeableConcept"""
        if not codeable_concept:
            return ''
        
        if 'coding' in codeable_concept and len(codeable_concept['coding']) > 0:
            return codeable_concept['coding'][0].get('code', '')
        
        return ''
    
    def list_all_patients(self) -> List[Dict[str, str]]:
        """
        List all patient collections in the database
        
        Returns:
            List of patients with their collection names and metadata
        """
        if not self.client:
            self.client = chromadb.CloudClient(
                api_key=self.api_key,
                tenant=self.tenant,
                database=self.database
            )
        
        collections = self.client.list_collections()
        patients = []
        
        for collection in collections:
            meta = collection.metadata
            patients.append({
                'collection_name': collection.name,
                'patient_id': meta.get('patient_id', collection.name),
                'patient_name': meta.get('patient_name', 'Unknown'),
                'age': meta.get('age', 0),
                'gender': meta.get('gender', 'Unknown'),
                'last_updated': meta.get('last_updated', 'Unknown')
            })
        
        return patients
    
    def get_patient_collection(self, patient_id: str):
        """
        Get a specific patient's collection
        
        Args:
            patient_id: Patient ID
            
        Returns:
            ChromaDB collection for the patient
        """
        if not self.client:
            self.client = chromadb.CloudClient(
                api_key=self.api_key,
                tenant=self.tenant,
                database=self.database
            )
        
        collection_name = patient_id.replace(':', '-').replace(' ', '_')
        return self.client.get_collection(collection_name)


def main():
    """Main function to run the FHIR to ChromaDB parser"""
    
    # ChromaDB Cloud credentials - REPLACE WITH YOUR CREDENTIALS
    API_KEY = os.environ.get('CHROMADB_API_KEY', 'ck-5KbgqxnfaJT9VXwgoWtpVAi84gnHBYnLY5iATpSAnutn')
    TENANT = os.environ.get('CHROMADB_TENANT', '02a43515-0e15-440c-999f-b1dc0242aa7d')
    DATABASE = os.environ.get('CHROMADB_DATABASE', 'CalHacks2025')  # Shared database
    

    # Path to FHIR JSON file
    FHIR_JSON_PATH = r"c:\Users\saray\Downloads\Gregorio366_Batz141_12bee8ac-7bce-f218-179e-0c2cabade79f.json"
    
    # Initialize parser
    parser = FHIRToChromaDB(
        api_key=API_KEY,
        tenant=TENANT,
        database=DATABASE
    )
    
    # Process FHIR bundle - creates one collection per patient
    try:
        result = parser.process_fhir_bundle(FHIR_JSON_PATH)
        print("\n" + "="*60)
        print("UPLOAD COMPLETE")
        print("="*60)
        print(f"Database: {DATABASE}")
        print(f"Collection: {result['collection_name']}")
        print(f"Patient: {result['patient_name']}")
        print(f"Documents Created: {result['total_documents']}")
        print(f"Document Types: {', '.join(result['document_types'])}")
        print("="*60)
    except Exception as e:
        print(f"Error processing FHIR bundle: {e}")
        raise


if __name__ == '__main__':
    main()