from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from config import MONGODB_URI, DATABASE_NAME
from bson import ObjectId
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDB:
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self.connect()

    def connect(self):
        """Connect to MongoDB (local or Atlas)"""
        try:
            # Check if it's a local connection
            is_local = 'localhost' in MONGODB_URI or '127.0.0.1' in MONGODB_URI
            
            if is_local:
                # Local MongoDB without TLS
                self._client = MongoClient(
                    MONGODB_URI,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000
                )
            else:
                # MongoDB Atlas with TLS
                self._client = MongoClient(
                    MONGODB_URI,
                    tls=True,
                    tlsAllowInvalidCertificates=False,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000
                )
            
            self._db = self._client[DATABASE_NAME]
            
            # Test the connection
            self._client.admin.command('ping')
            logger.info("✅ MongoDB connection successful!")
            
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
            raise

    @property
    def db(self):
        """Get the database instance"""
        if self._db is None:
            self.connect()
        return self._db

    @property
    def client(self):
        """Get the client instance"""
        if self._client is None:
            self.connect()
        return self._client

    def close(self):
        """Close the MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")

# Initialize MongoDB instance
mongodb = MongoDB()

def get_db():
    """Get database instance"""
    return mongodb.db

def get_collection(collection_name):
    """Get a specific collection"""
    return mongodb.db[collection_name]

def find_one(collection_name, query):
    """Find a single document"""
    try:
        logger.info(f"🔍 FIND_ONE: {collection_name} | Query: {query}")
        result = get_collection(collection_name).find_one(query)
        logger.info(f"✅ Found: {bool(result)}")
        return result
    except Exception as e:
        logger.error(f"❌ Error in find_one: {e}")
        raise

def find_many(collection_name, query=None, sort=None, limit=None):
    """Find multiple documents"""
    try:
        logger.info(f"🔍 FIND_MANY: {collection_name} | Query: {query}")
        cursor = get_collection(collection_name).find(query or {})
        
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
            
        result = list(cursor)
        logger.info(f"✅ Found {len(result)} documents")
        return result
    except Exception as e:
        logger.error(f"❌ Error in find_many: {e}")
        raise

def insert_one(collection_name, document):
    """Insert a single document"""
    try:
        logger.info(f"➕ INSERT_ONE: {collection_name}")
        result = get_collection(collection_name).insert_one(document)
        logger.info(f"✅ Inserted with ID: {result.inserted_id}")
        return result
    except Exception as e:
        logger.error(f"❌ Error in insert_one: {e}")
        raise

def insert_many(collection_name, documents):
    """Insert multiple documents"""
    try:
        logger.info(f"➕ INSERT_MANY: {collection_name} | Count: {len(documents)}")
        result = get_collection(collection_name).insert_many(documents)
        logger.info(f"✅ Inserted {len(result.inserted_ids)} documents")
        return result
    except Exception as e:
        logger.error(f"❌ Error in insert_many: {e}")
        raise

def update_one(collection_name, query, update):
    """Update a single document"""
    try:
        logger.info(f"📝 UPDATE_ONE: {collection_name} | Query: {query}")
        result = get_collection(collection_name).update_one(query, update)
        logger.info(f"✅ Modified: {result.modified_count} documents")
        return result.modified_count
    except Exception as e:
        logger.error(f"❌ Error in update_one: {e}")
        raise

def delete_one(collection_name, query):
    """Delete a single document"""
    try:
        logger.info(f"🗑️ DELETE_ONE: {collection_name} | Query: {query}")
        result = get_collection(collection_name).delete_one(query)
        logger.info(f"✅ Deleted: {result.deleted_count} documents")
        return result.deleted_count
    except Exception as e:
        logger.error(f"❌ Error in delete_one: {e}")
        raise

def aggregate(collection_name, pipeline):
    """Perform aggregation"""
    try:
        logger.info(f"🔄 AGGREGATE: {collection_name}")
        result = list(get_collection(collection_name).aggregate(pipeline))
        logger.info(f"✅ Aggregation returned {len(result)} documents")
        return result
    except Exception as e:
        logger.error(f"❌ Error in aggregate: {e}")
        raise

def to_object_id(id_str):
    """Convert string to ObjectId"""
    if isinstance(id_str, ObjectId):
        return id_str
    if isinstance(id_str, str) and ObjectId.is_valid(id_str):
        return ObjectId(id_str)
    raise ValueError(f"Invalid ObjectId: {id_str}")

def from_object_id(obj_id):
    """Convert ObjectId to string"""
    if isinstance(obj_id, ObjectId):
        return str(obj_id)
    return obj_id

# Helper function to convert MongoDB documents for JSON serialization
def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable format"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == '_id':
                result['id'] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = serialize_doc(value)
            elif isinstance(value, list):
                result[key] = serialize_doc(value)
            else:
                result[key] = value
        return result
    return doc

# ========== PARTITIONING FUNCTIONS ==========

def hash_partition(value, num_partitions=8):
    """
    Calculate hash partition for a value
    Used for workers collection (8 partitions)
    """
    if isinstance(value, ObjectId):
        value = str(value)
    return hash(str(value)) % num_partitions

def get_worker_partition_collection(worker_id):
    """
    Get the partitioned collection name for a worker
    Workers are hash partitioned into 8 collections
    """
    partition_num = hash_partition(worker_id, 8)
    return f"workers_partition_{partition_num}"

def get_jobs_partition_collection(year):
    """
    Get the partitioned collection name for jobs by year
    Jobs are range partitioned by posted year
    """
    return f"jobs_{year}"

def get_all_worker_partitions():
    """Get all worker partition collection names"""
    return [f"workers_partition_{i}" for i in range(8)]

def get_jobs_partition_stats():
    """Get statistics about job partitions (which years exist)"""
    db = MongoDB().db
    collections = db.list_collection_names()
    job_collections = [c for c in collections if c.startswith("jobs_")]
    
    stats = []
    for coll_name in job_collections:
        if coll_name == "jobs":  # Skip the original jobs collection
            continue
        try:
            year = int(coll_name.split("_")[1])
            count = db[coll_name].count_documents({})
            stats.append({
                "collection": coll_name,
                "year": year,
                "document_count": count
            })
        except (ValueError, IndexError):
            continue
    
    return sorted(stats, key=lambda x: x["year"])
