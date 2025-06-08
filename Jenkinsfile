pipeline {
  agent any
  environment {
    AWS_REGION      = 'us-east-1'
    EKS_CLUSTER   = 'aws-glue-eks'  
    AWS_CREDENTIALS = 'aws-glue-iam'
    K8S_CREDS       = 'eks-kubeconfig'
    ECR_REPO        = '756999892440.dkr.ecr.us-east-1.amazonaws.com/orders-api'
  }
  stages {
    stage('Checkout') {
      steps { git branch: 'main', url: 'https://github.com/abhaydesai01/aws-glue.git' }
    }
    stage('Build & Test') {
      steps {
        dir('app') {
          sh 'pip install -r requirements.txt'
          sh 'pytest --maxfail=1 --disable-warnings --quiet'
        }
      }
    }
    stage('Dockerize & Push') {
      steps {
        script {
          IMAGE_TAG = "${env.GIT_COMMIT.take(8)}"
        }
        withAWS(credentials: AWS_CREDENTIALS, region: AWS_REGION) {
          sh """
            aws ecr get-login-password |
              docker login --username AWS --password-stdin $ECR_REPO
            docker build -t $ECR_REPO:$IMAGE_TAG app/
            docker push $ECR_REPO:$IMAGE_TAG
          """
        }
      }
    }
    stage('Deploy to EKS') {
      steps {
        withKubeConfig(credentialsId: K8S_CREDS) {
          sh """
            kubectl set image deployment/orders-api api=$ECR_REPO:$IMAGE_TAG -n default
            kubectl rollout status deployment/orders-api -n default
          """
        }
      }
    }
    stage('Glue Crawler') {
      steps {
        withAWS(credentials: AWS_CREDENTIALS, region: AWS_REGION) {
          sh "aws glue start-crawler --name sales-orders-crawler"
          // wait until READY (optional loop)
        }
      }
    }
    stage('Glue ETL') {
      steps {
        withAWS(credentials: AWS_CREDENTIALS, region: AWS_REGION) {
          sh "aws glue start-job-run --job-name sales-orders-etl"
        }
      }
    }
  }
}
