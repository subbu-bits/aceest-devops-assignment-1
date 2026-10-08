// Jenkins declarative pipeline for ACEest Fitness & Gym.
// Jenkins runs these stages ON YOUR VM, inside its workspace folder.
pipeline {
    agent any

    environment {
        IMAGE_NAME = 'aceest-fitness'
    }

    stages {
        stage('Checkout') {
            steps {
                // Pull the latest code from GitHub
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -m py_compile app.py
                    flake8 app.py tests/
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest -v --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t $IMAGE_NAME:$BUILD_NUMBER -t $IMAGE_NAME:latest .'
            }
        }

        stage('Test Inside Container') {
            steps {
                sh 'docker run --rm $IMAGE_NAME:$BUILD_NUMBER pytest -v'
            }
        }
    }

    post {
        success {
            echo "BUILD SUCCESS: image ${IMAGE_NAME}:${BUILD_NUMBER} is ready"
        }
        failure {
            echo 'BUILD FAILED: check the stage logs above'
        }
        always {
            // Clean the workspace so every build starts fresh
            deleteDir()
        }
    }
}
