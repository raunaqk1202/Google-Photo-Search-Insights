# Problem Statement: Google Photos Memory Retrieval Discovery Engine

## 1. Context & Background
Over years of usage, users accumulate thousands of photos, videos, screenshots, and documents in Google Photos. While the current search functionality works well for highly precise, transactional queries, retrieval becomes significantly harder when a user's memory is incomplete. A key strategic goal for the Core Experience team is to increase the percentage of users who successfully retrieve a photo they remember but cannot precisely describe at the start of their search. 

## 2. Core Problem
Human memory is episodic and associative (remembering the "vibe," a specific object, or related people), while traditional search interfaces demand precise metadata (exact dates, locations, or keywords). To bridge this gap and build solutions like "Iterative Guided Recall," the product team must deeply understand where the current retrieval experience breaks down. Currently, there is a lack of structured, evidence-based analysis detailing how users attempt these fuzzy searches, what they remember, and why they abandon the search funnel.

## 3. Objective
Design and build an AI-Powered Discovery Engine that autonomously scrapes, processes, and analyzes real user feedback at scale. This engine will act as a conversational product analytics tool, allowing the team to interrogate the data to extract structured customer personas, map the search abandonment funnel, and identify high-impact product opportunities.

## 4. Key Investigative Questions
The Discovery Engine must synthesize raw data to answer the following core product questions:
* **The Missing Asset:** What specific categories of old photos do users most frequently struggle to retrieve (e.g., specific trips, utility photos like medicine/receipts, screenshots)?
* **Memory Asymmetry:** What sensory or contextual information do people actually remember about a photo versus the rigid metadata they have forgotten?
* **Query Formulation:** How do users linguistically formulate searches when their memory is incomplete, and what happens when they face a blank search canvas?
* **Opportunity Mapping:** How do different retrieval friction points compare in volume, and what are the root causes in the search abandonment KPI driver tree?

## 5. Data & Operational Constraints
* **Absolute Ground Truth:** The engine must rely entirely on live data acquisition. The generation of mock or synthetic data is strictly prohibited.
* **Target Sources:** Must scrape actual user feedback from Google Play Store reviews, App Store reviews, Reddit discussions, Google Photos community/support forums, and relevant YouTube comments.
* **Analytical Rigor:** Unstructured text must be rigorously processed and structured (e.g., utilizing Pandas DataFrames) to extract quantitative signals, define user personas, and map drop-off points before being fed to the LLM.

## 6. Target End-State Experience
The overarching goal is to power a decoupled web application consisting of:
* A **Python API Backend** responsible for scraping the live sources, cleaning and structuring the datasets, and managing the vector database.
* An ultra-low latency **Groq-powered RAG pipeline** configured to act as a UX Researcher.
* A **React.js Frontend** featuring a conversational interface where PMs can ask the key investigative questions. Every insight returned by the UI must include direct citations linking back to the raw scraped reviews.