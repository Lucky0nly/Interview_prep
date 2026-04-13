import random

SUPPORTED_ROLES = {
    "Software Engineer": {
        "Easy": [
            "Explain the difference between an array and a linked list.",
            "What is version control, and why is Git commonly used in teams?",
            "How would you describe object-oriented programming to a junior developer?",
            "What is the purpose of an API in a software system?",
            "How do you approach debugging when a feature stops working unexpectedly?",
            "What is the difference between a compiled language and an interpreted language?",
            "Why are unit tests important in software development?",
            "What are HTTP status codes, and which ones do you use most often?",
            "Describe a time-space tradeoff you have seen in programming.",
            "What makes code maintainable over time?",
            "How would you explain REST to a non-technical stakeholder?",
            "What is the role of a database index?",
        ],
        "Medium": [
            "Design a URL shortener and explain the components you would prioritize first.",
            "How would you optimize a slow database-backed endpoint in a production API?",
            "Compare monolithic and microservice architectures with practical tradeoffs.",
            "What strategies do you use to make backend systems resilient to failure?",
            "How would you implement caching for a high-read application?",
            "Describe how you would investigate a memory leak in a Python service.",
            "How do you decide when to refactor versus when to ship quickly?",
            "Explain database transactions and when they matter in distributed systems.",
            "How would you secure a web application that exposes public APIs?",
            "Walk through how you would review a pull request for a critical backend feature.",
            "How would you roll out a breaking API change with minimal disruption?",
            "Describe a system design choice that improves scalability but increases complexity.",
        ],
        "Hard": [
            "Design a real-time collaborative editing platform and discuss consistency tradeoffs.",
            "How would you architect a multi-tenant SaaS system with strong isolation guarantees?",
            "Explain how you would debug intermittent latency spikes across several microservices.",
            "Design a fault-tolerant job processing system for millions of daily events.",
            "How would you handle schema evolution in a large event-driven architecture?",
            "Describe how you would build observability for a globally distributed platform.",
            "What tradeoffs arise when choosing between SQL and NoSQL for high-scale workloads?",
            "How would you design rate limiting for a public API serving many client types?",
            "Discuss strategies for ensuring idempotency in a payment or order-processing system.",
            "How would you detect and mitigate cascading failures in a service mesh?",
            "Design an access-control model for an enterprise platform with complex permissions.",
            "How would you lead a postmortem after a major production outage?",
        ],
    },
    "Data Scientist": {
        "Easy": [
            "What is the difference between supervised and unsupervised learning?",
            "How do training, validation, and test datasets differ?",
            "What does overfitting mean, and how can you detect it?",
            "Explain precision, recall, and F1 score in simple terms.",
            "Why is feature scaling important for some machine learning algorithms?",
            "How do you handle missing values in a dataset?",
            "What is the purpose of exploratory data analysis?",
            "How do correlation and causation differ?",
            "What is a confusion matrix used for?",
            "Describe a common bias that can affect real-world data collection.",
            "What makes a good data visualization for stakeholders?",
            "How would you explain a regression model to a business team?",
        ],
        "Medium": [
            "How would you build a churn prediction model from raw product usage data?",
            "Describe your approach to feature engineering for tabular datasets.",
            "How do you choose between a linear model, a tree-based model, and a neural network?",
            "Explain how you would validate a model when the dataset is highly imbalanced.",
            "How would you communicate model uncertainty to non-technical decision-makers?",
            "Describe how you would detect data leakage before model deployment.",
            "How do you evaluate whether adding more features actually helps performance?",
            "What steps would you take to productionize a model for batch inference?",
            "How would you design an experiment to measure the impact of a recommendation system?",
            "Discuss the tradeoffs between interpretability and predictive power.",
            "How would you diagnose model drift after deployment?",
            "Explain how you would compare two classification models fairly.",
        ],
        "Hard": [
            "Design an end-to-end machine learning pipeline for fraud detection at scale.",
            "How would you monitor and retrain a model in a continuously changing environment?",
            "Discuss the tradeoffs between offline metrics and online A/B test performance.",
            "How would you build a causal inference strategy for a product intervention?",
            "Describe how you would architect a feature store for multiple ML teams.",
            "How would you detect and mitigate bias in a hiring or lending model?",
            "Explain how you would forecast demand with sparse and seasonal data.",
            "How would you design a ranking model for a search or recommendation product?",
            "What are the risks of using large language models in decision-support workflows?",
            "How would you evaluate a model where the cost of false negatives is very high?",
            "Describe a strategy for combining structured and unstructured data in one system.",
            "How would you explain SHAP values or model explainability techniques to stakeholders?",
        ],
    },
    "Web Developer": {
        "Easy": [
            "What is semantic HTML, and why does it matter?",
            "Explain the difference between block, inline, and inline-block elements.",
            "How does CSS specificity work?",
            "What is the DOM, and how does JavaScript interact with it?",
            "Why is responsive design important for modern web applications?",
            "What is the difference between local storage and session storage?",
            "How do cookies differ from tokens in web authentication?",
            "What is event bubbling in JavaScript?",
            "How do you improve basic accessibility on a webpage?",
            "Explain the difference between GET and POST requests.",
            "Why are browser developer tools valuable in frontend work?",
            "What makes a web page performant from the user's perspective?",
        ],
        "Medium": [
            "How would you structure a frontend application for maintainability as it grows?",
            "Describe how you would optimize Core Web Vitals for a content-heavy site.",
            "How do you secure a frontend application that consumes JWT-protected APIs?",
            "Explain the tradeoffs between client-side rendering and server-side rendering.",
            "How would you debug a layout issue that appears only on mobile devices?",
            "What strategies do you use to manage frontend state effectively?",
            "How would you design a reusable component library for a product team?",
            "Describe your approach to handling forms with validation and error states.",
            "How would you reduce bundle size in a JavaScript application?",
            "What are the practical benefits of progressive enhancement?",
            "How would you design an upload flow with progress tracking and retries?",
            "Describe a strategy for graceful API failure handling in the browser.",
        ],
        "Hard": [
            "Design a high-performance frontend architecture for a real-time collaboration tool.",
            "How would you build a secure authentication experience across multiple subdomains?",
            "Describe how you would detect and fix memory leaks in a large single-page app.",
            "How would you architect offline-first behavior for a browser application?",
            "What tradeoffs arise when building design systems for multiple products?",
            "How would you make a complex dashboard accessible without sacrificing usability?",
            "Describe how you would instrument a frontend app for analytics and diagnostics.",
            "How would you manage cache invalidation for assets and API responses in the browser?",
            "Design a strategy for micro-frontends and discuss where they can go wrong.",
            "How would you harden a web app against XSS, CSRF, and clickjacking?",
            "What is your approach to coordinating frontend and backend version compatibility?",
            "How would you lead performance remediation on a revenue-critical landing page?",
        ],
    },
}

SUPPORTED_DIFFICULTIES = {"Easy", "Medium", "Hard"}


def normalize_role(role: str) -> str:
    for supported_role in SUPPORTED_ROLES:
        if role.strip().lower() == supported_role.lower():
            return supported_role
    raise ValueError(f"Unsupported role '{role}'.")


def normalize_difficulty(difficulty: str) -> str:
    for supported_difficulty in SUPPORTED_DIFFICULTIES:
        if difficulty.strip().lower() == supported_difficulty.lower():
            return supported_difficulty
    raise ValueError(f"Unsupported difficulty '{difficulty}'.")


def get_interview_duration(num_questions: int) -> int:
    return max(600, num_questions * 150)


def generate_questions(role: str, difficulty: str, num_questions: int) -> list[str]:
    normalized_role = normalize_role(role)
    normalized_difficulty = normalize_difficulty(difficulty)

    available_questions = list(SUPPORTED_ROLES[normalized_role][normalized_difficulty])
    random.shuffle(available_questions)
    requested_count = max(5, min(num_questions, 10))
    return available_questions[:requested_count]
