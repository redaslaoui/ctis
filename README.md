# Clinical Trial Intelligence Platform

## 🎯 Overview

Clinical Trial Intelligence Platform (CTIS) leverages Agentic AI and RAG (Retrieval-Augmented Generation) to help pharmaceutical companies design more successful clinical trials. By analyzing thousands of historical trials, CTIS predicts failure risk for proposed trial designs with transparent, step-by-step reasoning that explains why certain design elements are problematic. It then recommends data-driven adjustments to improve success rates.

### The problem

* 90% of clinical trials fail after entering human testing
* Average cost of a failed Phase 3 trial: $800M - $1.2B
* Historical trial data remains largely unanalyzed and siloed

### The solution
An intelligent platform that:

1. Predicts trial failure risk
2. Identifies similar historical trials and their outcomes
3. Recommends optimizations based on successful patterns
4. Monitor clinical trial KPIs (e.g. enrollment rates)


### 🛠 Technology Stack

#### Backend

* FastAPI (Python 3.12+)
* PostgreSQL
* Weaviate for RAG vector store
* Redis (for caching)
* Celery (for background tasking)
* LangChain/LangGraph - RAG and agents orchestration
* OpenAI

#### Frontend

* React 19
* Tailwind CSS
* Recharts

#### Infrastructure

* AWS - Cloud platform (ECS, RDS, S3, CloudFront)
* Pulumi - Infrastructure as Code
* Docker - Containerization
* GitHub Actions - CI/CD
