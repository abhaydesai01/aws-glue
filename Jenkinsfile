pipeline {
  agent any

  environment {
    AWS_REGION  = 'us-east-1'
    EKS_CLUSTER = 'aws-glue-eks'
    ECR_REPO    = '756999892440.dkr.ecr.us-east-1.amazonaws.com/orders-api'
  }

  stages {
    stage('Checkout') {
      steps {
        git branch: 'master',
            url:    'https://github.com/abhaydesai01/aws-glue.git'
      }
    }

    stage('Build & Push') {
      steps {
        script { env.IMAGE_TAG = env.GIT_COMMIT.take(8) }
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
        withCredentials([usernamePassword(
          credentialsId: 'aws-glue-iam',
          usernameVariable: 'AWS_ACCESS_KEY_ID',
          passwordVariable: 'AWS_SECRET_ACCESS_KEY'
        )]) {
          script {
            env.KUBECONFIG = "${WORKSPACE}/kubeconfig"
          }

          sh '''
            set -e
            # regenerate kubeconfig into workspace
            aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER --kubeconfig $KUBECONFIG

            # apply manifests
            kubectl --kubeconfig=$KUBECONFIG apply -f k8s/deployment.yaml --validate=false -n default
            kubectl --kubeconfig=$KUBECONFIG apply -f k8s/service.yaml    --validate=false -n default
          '''

          // attempt rollout, if it hangs then clean up old pods and retry
          script {
            try {
              timeout(time: 5, unit: 'MINUTES') {
                sh "kubectl --kubeconfig=\$KUBECONFIG -n default rollout status deployment/orders-api"
              }
            } catch (err) {
              echo "⚠️ Rollout timed out; force‐deleting old pods..."
              // find pods not matching the current image tag and delete them
              def oldPods = sh(
                script: """kubectl --kubeconfig=\$KUBECONFIG -n default get pods -l app=orders-api -o name \
                  | grep -v $IMAGE_TAG || true""",
                returnStdout: true
              ).trim()
              if (oldPods) {
                sh "kubectl --kubeconfig=\$KUBECONFIG -n default delete ${oldPods} --force --grace-period=0"
              } else {
                echo "No old pods found to delete."
              }
              // retry the rollout wait
              sh "kubectl --kubeconfig=\$KUBECONFIG -n default rollout status deployment/orders-api"
            }
          }
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
      echo "❌ Pipeline failed—check the console for details."
    }
  }
}
