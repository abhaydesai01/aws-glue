pipeline {
  agent any

  environment {
    AWS_REGION = 'us-east-1'
    ECR_REPO   = '756999892440.dkr.ecr.us-east-1.amazonaws.com/orders-api'
    K8S_CREDS  = 'eks-kubeconfig'
  }

  stages {
    stage('Checkout') {
      steps {
        git branch: 'master',
            url:    'https://github.com/abhaydesai01/aws-glue.git'
      }
    }

    stage('Build & Test') {
      steps {
        dir('app') {
          sh 'pip install -r requirements.txt'
        }
      }
    }

    stage('Dockerize & Push') {
      steps {
        script { env.IMAGE_TAG = env.GIT_COMMIT.take(8) }

        withCredentials([usernamePassword(
          credentialsId: 'aws-glue-iam',
          usernameVariable: 'AWS_ACCESS_KEY_ID',
          passwordVariable: 'AWS_SECRET_ACCESS_KEY'
        )]) {
          sh """
            aws configure set region ${AWS_REGION}
            aws ecr get-login-password \
              | docker login --username AWS \
                            --password-stdin ${ECR_REPO}

            docker build -t ${ECR_REPO}:${IMAGE_TAG} app/
            docker push  ${ECR_REPO}:${IMAGE_TAG}
          """
        }
      }
    }

    stage('Deploy to EKS') {
      steps {
        withKubeConfig(credentialsId: "${K8S_CREDS}") {
          sh """
            kubectl -n default set image deployment/orders-api \
              orders-api=${ECR_REPO}:${IMAGE_TAG}
            kubectl -n default rollout status deployment/orders-api
          """
        }
      }
    }

    stage('Glue Crawler & ETL') {
      steps {
        withCredentials([usernamePassword(
          credentialsId: 'aws-glue-iam',
          usernameVariable: 'AWS_ACCESS_KEY_ID',
          passwordVariable: 'AWS_SECRET_ACCESS_KEY'
        )]) {
          sh """
            aws configure set region ${AWS_REGION}
            aws glue start-crawler    --name sales-orders-crawler
            aws glue start-job-run    --job-name sales-orders-etl
          """
        }
      }
    }
  }

  post {
    success { echo "✅ Pipeline succeeded!" }
    failure { echo "❌ Pipeline failed—check the logs." }
  }
}
