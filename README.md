# RedditTitleSentiment
Sentiment Analysis on Reddit Post Titles



REQUIREMENTS
Reddit API Token (Instructions for obtaining this)
Digital Ocean API Token (Instructions for obtaining this)
SSH key uploaded to DigitalOcean

INSTALL
Place your reddit API and Digital Ocean API tokens into environment variables then run make. Ansible scripts are used to configure the servers so you must run this from a linux host.



## Evaluation Criteria

* Problem description
    * Description: Gather insights on how users feel about topics. 
    * 0 points: The problem is not described
    * 1 point: The problem is described but shortly or not clearly 
    * 2 points: The problem is well described and it's clear what the problem the project solves
* Cloud
    * Layout:  
    * 0 points: Cloud is not used, things run only locally
    * 2 points: The project is developed on the cloud OR uses localstack (or similar tool) OR the project is deployed to Kubernetes or similar container management platforms
    * 4 points: The project is developed on the cloud and IaC tools are used for provisioning the infrastructure
* Experiment tracking and model registry
    * Layout:  
    * 0 points: No experiment tracking or model registry
    * 2 points: Experiments are tracked or models are registered in the registry
    * 4 points: Both experiment tracking and model registry are used
* Workflow orchestration
    * Layout:  
    * 0 points: No workflow orchestration
    * 2 points: Basic workflow orchestration
    * 4 points: Fully deployed workflow 
* Model deployment
    * Layout: 
    * 0 points: Model is not deployed
    * 2 points: Model is deployed but only locally
    * 4 points: The model deployment code is containerized and could be deployed to cloud or special tools for model deployment are used
* Model monitoring
    * Layout: Evidently is used for model monitoring.
    * 0 points: No model monitoring
    * 2 points: Basic model monitoring that calculates and reports metrics
    * 4 points: Comprehensive model monitoring that sends alerts or runs a conditional workflow (e.g. retraining, generating debugging dashboard, switching to a different model) if the defined metrics threshold is violated
* Reproducibility
    * 0 points: No instructions on how to run the code at all, the data is missing
    * 2 points: Some instructions are there, but they are not complete OR instructions are clear and complete, the code works, but the data is missing
    * 4 points: Instructions are clear, it's easy to run the code, and it works. The versions for all the dependencies are specified.
* Best practices
    * [ ] There are unit tests (1 point)
    * [ ] There is an integration test (1 point)
    * [ ] Linter and/or code formatter are used (1 point)
    * [ ] There's a Makefile (1 point)
    * [ ] There are pre-commit hooks (1 point)
    * [ ] There's a CI/CD pipeline (2 points)