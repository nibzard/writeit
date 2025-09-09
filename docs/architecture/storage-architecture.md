# Storage Architecture

WriteIt uses **LMDB (Lightning Memory-Mapped Database)** as its primary storage engine, designed for high-performance, ACID-compliant data persistence with zero-copy reads and efficient versioning.

## 🎯 Why LMDB?

### Technical Advantages
- **Memory-mapped I/O**: Zero-copy reads with OS-managed caching
- **ACID transactions**: Full consistency guarantees
- **Single-writer, multiple-readers**: Perfect for WriteIt's access patterns
- **Copy-on-write**: Efficient branching and versioning
- **No external dependencies**: Embedded database, no server required
- **Cross-platform**: Works on Linux, macOS, Windows

### Performance Characteristics
- **Read performance**: 10M+ reads/second on modern hardware
- **Write performance**: 100K+ writes/second with batching
- **Memory efficiency**: Only active data pages loaded
- **Storage overhead**: ~5-10% metadata overhead
- **Crash recovery**: Immediate consistency after crash

## 🏗️ Storage Architecture Overview

```
WriteIt Application
        │
        ▼
┌─────────────────────────────────────────────────────┐
│              Storage Layer                          │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐│
│  │Event Store  │  │Query Engine │  │Cache Manager ││
│  │(Immutable)  │  │(Projections)│  │(LRU Cache)   ││
│  └─────────────┘  └─────────────┘  └──────────────┘│
├─────────────────────────────────────────────────────┤
│                LMDB Database                        │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐│
│  │   Events    │  │   Indexes   │  │  Snapshots   ││
│  │ Database    │  │ Database    │  │  Database    ││
│  └─────────────┘  └─────────────┘  └──────────────┘│
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│            File System Storage                      │
│  ~/.writeit/                                       │
│  ├── data/                                         │
│  │   ├── events.lmdb        (Event store)         │
│  │   ├── indexes.lmdb       (Query indexes)       │
│  │   └── snapshots.lmdb     (Performance cache)   │
│  ├── exports/                                      │
│  │   └── pipeline-runs/     (YAML exports)        │
│  └── config/                                       │
│      ├── pipelines/         (Pipeline configs)    │
│      └── styles/            (Style primers)       │
└─────────────────────────────────────────────────────┘
```

## 🗃️ Database Schema Design

### Key Hierarchical Structure
WriteIt uses lexicographically sorted keys to enable efficient range queries and logical grouping:

```python
# Key patterns for different data types
KEY_PATTERNS = {
    # Events (time-ordered)
    "event": "evt:{pipeline_run_id}:{timestamp}:{event_id}",
    "event_by_type": "evt_type:{event_type}:{timestamp}:{event_id}",
    
    # Pipeline runs
    "pipeline_run": "run:{pipeline_run_id}",
    "run_by_config": "run_cfg:{config_id}:{created_at}:{run_id}",
    "run_by_status": "run_sts:{status}:{created_at}:{run_id}",
    
    # Step states and responses  
    "step_state": "step:{pipeline_run_id}:{step_name}",
    "ai_response": "resp:{response_id}",
    "step_responses": "step_resp:{pipeline_run_id}:{step_name}:{response_index}",
    
    # Branching relationships
    "branch_parent": "branch_p:{child_run_id}",
    "branch_children": "branch_c:{parent_run_id}",
    "branch_tree": "tree:{root_run_id}",
    
    # Configuration and style data
    "pipeline_config": "cfg:{config_id}",
    "style_primer": "style:{primer_id}",
    
    # User sessions and preferences
    "user_session": "sess:{session_id}",
    "user_preferences": "pref:{user_id}",
    
    # Indexes for efficient queries
    "recent_pipelines": "idx_recent:{user_id}:{timestamp}",
    "completed_pipelines": "idx_done:{user_id}:{timestamp}",
    "active_pipelines": "idx_active:{user_id}:{timestamp}",
    
    # Snapshots for performance
    "pipeline_snapshot": "snap:{pipeline_run_id}:{event_count}",
    "snapshot_index": "snap_idx:{pipeline_run_id}"
}
```

### Multi-Database Strategy
WriteIt uses LMDB's multi-database feature to separate concerns:

```python
class WriteItStorage:
    def __init__(self, storage_path: Path):
        self.env = lmdb.open(
            str(storage_path / "writeit.lmdb"),
            max_dbs=5,
            map_size=1024 * 1024 * 1024,  # 1GB initial size
            max_readers=128,
            readonly=False
        )
        
        # Separate databases for different data types
        with self.env.begin(write=True) as txn:
            self.events_db = self.env.open_db(b'events', txn=txn)
            self.indexes_db = self.env.open_db(b'indexes', txn=txn) 
            self.snapshots_db = self.env.open_db(b'snapshots', txn=txn)
            self.config_db = self.env.open_db(b'config', txn=txn)
            self.user_db = self.env.open_db(b'user', txn=txn)
```

## 📝 Event Storage Implementation

### Event Persistence
```python
class EventStore:
    """Immutable event storage with LMDB backend"""
    
    def __init__(self, storage: WriteItStorage):
        self.storage = storage
        self.serializer = JSONSerializer()
    
    async def append_event(self, event: BaseEvent) -> None:
        """Append event to immutable log"""
        with self.storage.env.begin(write=True) as txn:
            # Primary event storage
            event_key = f"evt:{event.pipeline_run_id}:{event.timestamp.isoformat()}:{event.event_id}"
            event_data = self.serializer.serialize(event)
            txn.put(event_key.encode(), event_data, db=self.storage.events_db)
            
            # Type-based index for efficient queries
            type_key = f"evt_type:{event.event_type.value}:{event.timestamp.isoformat()}:{event.event_id}"
            txn.put(type_key.encode(), event.pipeline_run_id.bytes, db=self.storage.indexes_db)
            
            # Update pipeline indexes
            await self._update_pipeline_indexes(txn, event)
    
    async def get_events(
        self, 
        pipeline_run_id: UUID, 
        after: Optional[datetime] = None
    ) -> List[BaseEvent]:
        """Get all events for pipeline run"""
        with self.storage.env.begin() as txn:
            events = []
            key_prefix = f"evt:{pipeline_run_id}:"
            
            cursor = txn.cursor(db=self.storage.events_db)
            if cursor.set_range(key_prefix.encode()):
                for key, value in cursor:
                    if not key.decode().startswith(key_prefix):
                        break
                    
                    event = self.serializer.deserialize(value)
                    
                    # Filter by timestamp if specified
                    if after and event.timestamp <= after:
                        continue
                    
                    events.append(event)
            
            return events
    
    async def get_events_by_type(
        self,
        event_type: EventType,
        limit: int = 100
    ) -> List[BaseEvent]:
        """Get recent events of specific type across all pipelines"""
        with self.storage.env.begin() as txn:
            events = []
            type_prefix = f"evt_type:{event_type.value}:"
            
            cursor = txn.cursor(db=self.storage.indexes_db)
            # Start from most recent (reverse iteration)
            if cursor.set_range((type_prefix + "z").encode()):
                cursor.prev()
                
                count = 0
                while cursor.key().decode().startswith(type_prefix) and count < limit:
                    pipeline_run_id = UUID(bytes=cursor.value())
                    
                    # Get the actual event
                    event = await self._get_event_by_id(txn, pipeline_run_id, event_type)
                    if event:
                        events.append(event)
                        count += 1
                    
                    if not cursor.prev():
                        break
            
            return events
```

### Efficient Batch Operations
```python
class BatchEventWriter:
    """Optimized batch writing for high-throughput scenarios"""
    
    def __init__(self, event_store: EventStore, batch_size: int = 100):
        self.event_store = event_store
        self.batch_size = batch_size
        self.pending_events: List[BaseEvent] = []
        self.pending_indexes: Dict[str, Any] = {}
    
    async def add_event(self, event: BaseEvent) -> None:
        """Add event to batch"""
        self.pending_events.append(event)
        
        if len(self.pending_events) >= self.batch_size:
            await self.flush()
    
    async def flush(self) -> None:
        """Write all pending events in single transaction"""
        if not self.pending_events:
            return
        
        with self.event_store.storage.env.begin(write=True) as txn:
            for event in self.pending_events:
                # Batch write events
                event_key = f"evt:{event.pipeline_run_id}:{event.timestamp.isoformat()}:{event.event_id}"
                event_data = self.event_store.serializer.serialize(event)
                txn.put(event_key.encode(), event_data, db=self.event_store.storage.events_db)
                
                # Batch update indexes
                await self._batch_update_indexes(txn, event)
        
        # Clear batch
        self.pending_events.clear()
        self.pending_indexes.clear()
```

## 🔍 Query Engine Implementation

### Efficient Data Retrieval
```python
class QueryEngine:
    """High-performance query engine for pipeline data"""
    
    def __init__(self, storage: WriteItStorage):
        self.storage = storage
    
    async def get_recent_pipelines(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[PipelineRun]:
        """Get user's most recent pipelines"""
        with self.storage.env.begin() as txn:
            pipelines = []
            key_prefix = f"idx_recent:{user_id}:"
            
            cursor = txn.cursor(db=self.storage.indexes_db)
            # Start from newest (lexicographically largest timestamp)
            if cursor.set_range((key_prefix + "z").encode()):
                cursor.prev()
                
                count = 0
                while cursor.key().decode().startswith(key_prefix) and count < limit:
                    pipeline_run_id = UUID(cursor.value().decode())
                    pipeline = await self.get_pipeline_run(pipeline_run_id)
                    
                    if pipeline:
                        pipelines.append(pipeline)
                        count += 1
                    
                    if not cursor.prev():
                        break
            
            return pipelines
    
    async def find_pipelines_by_config(
        self, 
        config_id: str,
        status_filter: Optional[PipelineStatus] = None
    ) -> List[PipelineRun]:
        """Find all pipeline runs using specific configuration"""
        with self.storage.env.begin() as txn:
            pipelines = []
            key_prefix = f"run_cfg:{config_id}:"
            
            cursor = txn.cursor(db=self.storage.indexes_db)
            if cursor.set_range(key_prefix.encode()):
                for key, value in cursor:
                    if not key.decode().startswith(key_prefix):
                        break
                    
                    pipeline_run_id = UUID(value.decode())
                    pipeline = await self.get_pipeline_run(pipeline_run_id)
                    
                    if pipeline and (not status_filter or pipeline.status == status_filter):
                        pipelines.append(pipeline)
            
            return pipelines
    
    async def get_pipeline_branches(self, root_pipeline_id: UUID) -> Dict[UUID, List[UUID]]:
        """Get complete branch tree for pipeline"""
        with self.storage.env.begin() as txn:
            branch_tree = {}
            
            def build_branch_tree(pipeline_id: UUID):
                children_key = f"branch_c:{pipeline_id}"
                children_data = txn.get(children_key.encode(), db=self.storage.indexes_db)
                
                if children_data:
                    children_ids = json.loads(children_data.decode())
                    branch_tree[pipeline_id] = [UUID(child_id) for child_id in children_ids]
                    
                    # Recursively build subtrees
                    for child_id in children_ids:
                        build_branch_tree(UUID(child_id))
                else:
                    branch_tree[pipeline_id] = []
            
            build_branch_tree(root_pipeline_id)
            return branch_tree
```

### Index Management
```python
class IndexManager:
    """Manages secondary indexes for efficient queries"""
    
    async def update_pipeline_indexes(
        self, 
        txn: lmdb.Transaction, 
        pipeline: PipelineRun
    ) -> None:
        """Update all indexes for pipeline changes"""
        
        # Recent pipelines index (time-ordered)
        recent_key = f"idx_recent:{pipeline.user_id}:{pipeline.created_at.isoformat()}"
        txn.put(recent_key.encode(), str(pipeline.pipeline_run_id).encode(), 
                db=self.storage.indexes_db)
        
        # Status-based index
        status_key = f"run_sts:{pipeline.status.value}:{pipeline.created_at.isoformat()}:{pipeline.pipeline_run_id}"
        txn.put(status_key.encode(), b"", db=self.storage.indexes_db)
        
        # Configuration-based index  
        config_key = f"run_cfg:{pipeline.configuration_id}:{pipeline.created_at.isoformat()}"
        txn.put(config_key.encode(), str(pipeline.pipeline_run_id).encode(),
                db=self.storage.indexes_db)
        
        # Branch relationship indexes
        if pipeline.parent_pipeline_run_id:
            parent_key = f"branch_p:{pipeline.pipeline_run_id}"
            txn.put(parent_key.encode(), str(pipeline.parent_pipeline_run_id).encode(),
                    db=self.storage.indexes_db)
            
            # Update parent's children list
            children_key = f"branch_c:{pipeline.parent_pipeline_run_id}"
            existing_children = txn.get(children_key.encode(), b"[]", db=self.storage.indexes_db)
            children = json.loads(existing_children.decode())
            
            if str(pipeline.pipeline_run_id) not in children:
                children.append(str(pipeline.pipeline_run_id))
                txn.put(children_key.encode(), json.dumps(children).encode(),
                        db=self.storage.indexes_db)
```

## ⚡ Performance Optimizations

### Snapshot Strategy
```python
class SnapshotManager:
    """Manages pipeline state snapshots for performance"""
    
    async def should_create_snapshot(self, pipeline_run_id: UUID) -> bool:
        """Determine if snapshot should be created"""
        event_count = await self.event_store.count_events(pipeline_run_id)
        latest_snapshot = await self.get_latest_snapshot(pipeline_run_id)
        
        # Create snapshot every 100 events or if none exists
        if not latest_snapshot:
            return event_count >= 10  # First snapshot after 10 events
        
        events_since_snapshot = event_count - latest_snapshot.event_count
        return events_since_snapshot >= 100
    
    async def create_snapshot(
        self, 
        pipeline_run_id: UUID, 
        state: PipelineRun
    ) -> None:
        """Create optimized snapshot"""
        event_count = await self.event_store.count_events(pipeline_run_id)
        
        snapshot = PipelineSnapshot(
            pipeline_run_id=pipeline_run_id,
            state_data=self.serializer.serialize(state),
            event_count=event_count,
            created_at=datetime.utcnow()
        )
        
        with self.storage.env.begin(write=True) as txn:
            # Store snapshot
            snapshot_key = f"snap:{pipeline_run_id}:{event_count}"
            txn.put(snapshot_key.encode(), snapshot.state_data, db=self.storage.snapshots_db)
            
            # Update snapshot index
            index_key = f"snap_idx:{pipeline_run_id}"
            index_data = {
                "latest_event_count": event_count,
                "created_at": snapshot.created_at.isoformat()
            }
            txn.put(index_key.encode(), json.dumps(index_data).encode(), 
                    db=self.storage.snapshots_db)
```

### Connection Pooling and Caching
```python
class StorageManager:
    """Manages LMDB connections and caching"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.connection_pool = ConnectionPool(max_connections=10)
        self.cache = LRUCache(max_size=1000)
        self.stats = StorageStats()
    
    async def get_with_cache(self, key: str) -> Optional[Any]:
        """Get data with LRU caching"""
        # Check cache first
        cached_value = self.cache.get(key)
        if cached_value:
            self.stats.cache_hits += 1
            return cached_value
        
        # Fetch from LMDB
        self.stats.cache_misses += 1
        with self.connection_pool.get_connection() as conn:
            value = await self._fetch_from_lmdb(conn, key)
            
            if value:
                self.cache.set(key, value)
                
            return value
```

## 📊 Storage Monitoring

### Performance Metrics
```python
@dataclass
class StorageMetrics:
    """Storage performance and health metrics"""
    
    # Performance metrics
    read_operations: int = 0
    write_operations: int = 0
    avg_read_time_ms: float = 0.0
    avg_write_time_ms: float = 0.0
    
    # Cache metrics
    cache_hit_rate: float = 0.0
    cache_size: int = 0
    cache_evictions: int = 0
    
    # Storage metrics
    database_size_mb: float = 0.0
    total_events: int = 0
    total_pipelines: int = 0
    active_connections: int = 0
    
    # Health indicators
    last_backup: Optional[datetime] = None
    corruption_checks_passed: bool = True
    disk_space_available_gb: float = 0.0

class StorageMonitor:
    """Monitors storage health and performance"""
    
    async def collect_metrics(self) -> StorageMetrics:
        """Collect current storage metrics"""
        return StorageMetrics(
            database_size_mb=await self._get_database_size(),
            total_events=await self._count_total_events(),
            total_pipelines=await self._count_total_pipelines(),
            cache_hit_rate=self.cache.hit_rate(),
            active_connections=self.connection_pool.active_count(),
            disk_space_available_gb=await self._get_available_disk_space()
        )
    
    async def health_check(self) -> bool:
        """Perform comprehensive storage health check"""
        try:
            # Test basic read/write
            test_key = f"health_check:{uuid4()}"
            test_data = {"timestamp": datetime.utcnow().isoformat()}
            
            await self.storage.set(test_key, test_data)
            retrieved_data = await self.storage.get(test_key)
            await self.storage.delete(test_key)
            
            return retrieved_data == test_data
        except Exception:
            return False
```

This storage architecture provides WriteIt with a high-performance, reliable foundation that scales from single-user development to production deployments while maintaining the simplicity and robustness required by the constitutional principles.