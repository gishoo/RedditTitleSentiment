# RedditTitleSentiment
Sentiment Analysis on Reddit Post Titles



REQUIREMENTS
OS:
Linux (Because Ansible is used)

Credentials:
Reddit API Credentials ([Instructions for obtaining this](https://github.com/reddit-archive/reddit/wiki/OAuth2))
Digital Ocean API Token ([Instructions for obtaining this](https://docs.digitalocean.com/reference/api/create-personal-access-token/))
SSH key uploaded to DigitalOcean ([Instructions](https://docs.digitalocean.com/platform/teams/how-to/upload-ssh-keys/))


INSTALL

Clone the repository.

```https://github.com/gishoo/RedditTitleSentiment
cd RedditTitleSentiment
```

Place your reddit API and Digital Ocean API credentials into environment variables. 

```REDDIT_CLIENT_ID=YourClientID
REDDIT_CLIENT_SECRET=YourClientSecret
REDDIT_USER_AGENT=YourUserAgent
```

```
TF_VAR_do_token=YourDigitalOceanApiToken
TF_VAR_ssh_key_ids=YourSshPublicKeys
```

Once that's done run the makefile.

```make```

## Evaluation Criteria

* Problem description
    * Description: A company has multiple social media profiles and platforms for community outreach, but is overwhelmed trying to analyze all of them. This project is a way for them to quickly gauge how there customers feel about them and their products. 

* Cloud
    * Description: This project is developed on Digital Ocean's Cloud and Terraform and Ansible are used for provisioning and configuration respectively. 

* Experiment tracking and model registry
    * Description: The project uses Mlflow for experiment tracking and model registry.  

* Model deployment
    * Description: The model is deployed to Digital Ocean's Cloud using a custom API.
    The URL for the deployment is: ([ranking.quest](http://ranking.quest))

* Reproducibility
    * Description: The setup instructions are above in the installation section. But in case something was missed. 

* Best practices
    * [Yes] There are unit tests 
    * [No] There is an integration test 
    * [No] Linter and/or code formatter are used
    * [Yes] There's a Makefile
    * [No] There are pre-commit hooks 
    * [No] There's a CI/CD pipeline