# Database Design

## Current Stage

No database models or migrations have been created yet. The Docker Compose configuration includes PostgreSQL and Redis, but the application does not connect to them at this stage.

## Intended Schema (Future)

### Projects

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_platforms TEXT[],  -- Array of platform names
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Contents

```sql
CREATE TABLE contents (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    source_text TEXT NOT NULL,
    source_url VARCHAR(1024),
    content_type VARCHAR(50),  -- article, idea, url
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Platform Contents (adapted versions)

```sql
CREATE TABLE platform_contents (
    id UUID PRIMARY KEY,
    content_id UUID REFERENCES contents(id),
    platform VARCHAR(50) NOT NULL,  -- wechat, zhihu, bilibili, xiaohongshu, douyin
    title VARCHAR(500),
    body TEXT,
    hooks TEXT[],
    tags TEXT[],
    status VARCHAR(50),  -- draft, approved, published, rejected
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Agent Runs

```sql
CREATE TABLE agent_runs (
    id UUID PRIMARY KEY,
    content_id UUID REFERENCES contents(id),
    status VARCHAR(50),  -- running, completed, failed
    steps JSONB,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    total_latency_ms INTEGER,
    token_usage INTEGER
);
```

### Agent Steps

```sql
CREATE TABLE agent_steps (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES agent_runs(id),
    node_name VARCHAR(100),
    input JSONB,
    output JSONB,
    latency_ms INTEGER,
    tool_calls JSONB,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

### Evaluations

```sql
CREATE TABLE evaluations (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES agent_runs(id),
    consistency_score FLOAT,
    compliance_score FLOAT,
    readability_score FLOAT,
    overall_score FLOAT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### User Feedback

```sql
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES agent_runs(id),
    rating INTEGER,  -- 1-5
    comments TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Indexes (Future)

```sql
CREATE INDEX idx_contents_project ON contents(project_id);
CREATE INDEX idx_platform_contents_content ON platform_contents(content_id);
CREATE INDEX idx_platform_contents_platform ON platform_contents(platform);
CREATE INDEX idx_agent_runs_content ON agent_runs(content_id);
CREATE INDEX idx_agent_steps_run ON agent_steps(run_id);
CREATE INDEX idx_evaluations_run ON evaluations(run_id);
```

## Not in MVP

All database models, migrations, and queries are not yet implemented. SQLAlchemy setup and Alembic migration tooling will be added in a future stage.
