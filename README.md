# 🚦 AI Feature Flag & Quality Gateway

A production-ready feature flag system built specifically for Generative AI deployments. Traditional feature flags treat code deployment as binary (pass/fail). This system treats AI deployment as a continuous quality gradient. 

It routes traffic, evaluates LLM responses asynchronously using an LLM-as-a-judge, and **automatically triggers rollbacks** if response quality degrades below a set threshold.

## 🏗 System Architecture

* **Backend API (FastAPI):** Manages feature flag configurations and logs AI interactions.
* **Smart Client (Python SDK):** Uses consistent hashing (MD5) to route users to Baseline or Experimental prompts without flickering, and features graceful degradation.
* **Async Quality Worker (MLOps):** A background thread that grades the AI's response (1-5 scale) without blocking the user's application.
* **The "Kill Switch":** Continuously calculates rolling average quality scores and auto-locks flags at 0% rollout if the model begins hallucinating.
* **Real-Time Dashboard (Streamlit):** Visualizes active rollouts, quality scores over time, and automatic rollback events.
* **Infrastructure:** Fully containerized with Docker, backed by PostgreSQL and Redis.
