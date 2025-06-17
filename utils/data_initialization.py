import asyncio
import json
import os
from database.mongodb_handler import mongodb_handler
from database.vector_store import vector_store
from config.settings import settings
import logging

class DataInitializer:
    @staticmethod
    async def initialize_sample_data():
        """Initialize sample alumni data in both MongoDB and Vector Store"""
        try:
            # Load sample data
            sample_file = os.path.join("data", "sample_alumni.json")
            
            if not os.path.exists(sample_file):
                logging.warning("Sample data file not found")
                return False
            
            with open(sample_file, 'r') as f:
                sample_alumni = json.load(f)
            
            # Add to MongoDB
            alumni_ids = []
            for alumni in sample_alumni:
                try:
                    alumni_id = await mongodb_handler.create_alumni(alumni)
                    alumni_ids.append(alumni_id)
                    # Add the ID back to the alumni data for vector store
                    alumni['_id'] = alumni_id
                except Exception as e:
                    logging.warning(f"Failed to add alumni {alumni.get('name', 'Unknown')}: {e}")
            
            # Add to Vector Store for RAG
            success = await vector_store.add_alumni_documents(sample_alumni)
            
            if success:
                logging.info(f"Successfully initialized {len(alumni_ids)} alumni records")
                return True
            else:
                logging.error("Failed to add alumni to vector store")
                return False
                
        except Exception as e:
            logging.error(f"Data initialization failed: {e}")
            return False
    
    @staticmethod
    async def check_data_exists():
        """Check if data already exists in the system"""
        try:
            # Check MongoDB
            from config.database import db_connection
            collection = db_connection.db[settings.ALUMNI_COLLECTION]
            mongo_count = collection.count_documents({})
            
            # Check Vector Store
            vector_stats = await vector_store.get_collection_stats()
            vector_count = vector_stats.get('total_documents', 0)
            
            return {
                'mongodb_count': mongo_count,
                'vector_store_count': vector_count,
                'data_exists': mongo_count > 0 and vector_count > 0
            }
            
        except Exception as e:
            logging.error(f"Failed to check existing data: {e}")
            return {'mongodb_count': 0, 'vector_store_count': 0, 'data_exists': False}

# Global initializer
data_initializer = DataInitializer()
