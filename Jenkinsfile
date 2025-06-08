pipeline {
  agent any

  environment {
    AWS_REGION = 'us-east-1'
    ECR_REPO   = '756999892440.dkr.ecr.us-east-1.amazonaws.com/orders-api'
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
          // add tests here if you have any, e.g. pytest
        }
      }
    }

    stage('Dockerize & Push') {
      steps {
        // Compute and export IMAGE_TAG
        script {
          env.IMAGE_TAG = env.GIT_COMMIT.take(8)
        }

        // Inject AWS credentials for ECR
        withCredentials([usernamePassword(
          credentialsId: 'aws-glue-iam',
          usernameVariable: 'AWS_ACCESS_KEY_ID',
          passwordVariable: 'AWS_SECRET_ACCESS_KEY'
        )]) {
          sh '''
            set -e
            aws configure set region $AWS_REGION
            aws ecr get-login-password \
              | docker login --username AWS --password-stdin $ECR_REPO

            docker build -t $ECR_REPO:$IMAGE_TAG app/
            docker push  $ECR_REPO:$IMAGE_TAG
          '''
        }
      }
    }

    stage('Deploy to EKS') {
      steps {
        // Inject the kubeconfig file into $KUBECONFIG
        withCredentials([file(
          credentialsId: 'eks-kubeconfig',
          variable: 'KUBECONFIG'
        )]) {
          sh '''
            set -e
            kubectl --kubeconfig="$KUBECONFIG" -n default set image \
              deployment/orders-api orders-api="$ECR_REPO:$IMAGE_TAG"
            kubectl --kubeconfig="$KUBECONFIG" -n default rollout status \
              deployment/orders-api
          '''
        }
      }
    }

    stage('Glue Crawler & ETL') {
      steps {
        // Inject AWS credentials again for Glue
        withCredentials([usernamePassword(
          credentialsId: 'aws-glue-iam',
          usernameVariable: 'AWS_ACCESS_KEY_ID',
          passwordVariable: 'AWS_SECRET_ACCESS_KEY'
        )]) {
          sh '''
            set -e
            aws configure set region $AWS_REGION
            aws glue start-crawler --name sales-orders-crawler
            aws glue start-job-run --job-name sales-orders-etl
          '''
        }
      }
    }
  }

  post {
    success {
      echo "✅ Pipeline completed successfully!"
    }
    failure {
      echo "❌ Pipeline failed—check the console output for details."
    }
  }
}
