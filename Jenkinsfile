pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(
            logRotator(
                numToKeepStr: '20'
            )
        )
    }

    environment {
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
        PYTHONDONTWRITEBYTECODE = '1'
        CI = 'true'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm

                sh '''
                    echo "======================================"
                    echo " Mini-SOAR CI Pipeline"
                    echo "======================================"

                    echo "Branch:"
                    git branch --show-current || true

                    echo "Commit:"
                    git rev-parse --short HEAD

                    echo "Workspace:"
                    pwd
                '''
            }
        }

        stage('Environment Check') {
            steps {
                sh '''
                    echo "========== Python =========="
                    python3 --version

                    echo "========== pip =========="
                    python3 -m pip --version

                    echo "========== Node =========="
                    node --version

                    echo "========== npm =========="
                    npm --version

                    echo "==========================="
                '''
            }
        }

        stage('Backend Dependencies') {
            steps {
                sh '''
                    echo "Installing backend dependencies..."

                    rm -rf .jenkins-venv

                    python3 -m venv .jenkins-venv

                    . .jenkins-venv/bin/activate

                    python -m pip install --upgrade pip

                    python -m pip install \
                        -r requirements.txt
                '''
            }
        }

        stage('Backend Validation') {
            steps {
                sh '''
                    echo "Running Python validation..."

                    . .jenkins-venv/bin/activate

                    python -m compileall src app

                    python -m pip check
                '''
            }
        }

        stage('Frontend Dependencies') {
            steps {
                dir('frontend') {
                    sh '''
                        echo "Installing frontend dependencies..."

                        npm ci
                    '''
                }
            }
        }

        stage('Frontend Build') {
            steps {
                dir('frontend') {
                    sh '''
                        echo "Building Mini-SOAR dashboard..."

                        npm run build
                    '''
                }
            }
        }

        stage('Build Summary') {
            steps {
                sh '''
                    echo ""
                    echo "======================================"
                    echo " Mini-SOAR CI validation successful"
                    echo "======================================"
                    echo ""
                    echo "Backend:"
                    echo "  Python compile       PASS"
                    echo "  Dependency check     PASS"
                    echo ""
                    echo "Frontend:"
                    echo "  npm ci               PASS"
                    echo "  TypeScript build     PASS"
                    echo "  Vite build           PASS"
                    echo ""
                '''
            }
        }
    }

    post {
        success {
            echo 'Mini-SOAR CI pipeline completed successfully.'
        }

        failure {
            echo 'Mini-SOAR CI pipeline FAILED. Check the failed stage above.'
        }

        always {
            sh '''
                rm -rf .jenkins-venv || true
            '''

            cleanWs(
                deleteDirs: true,
                disableDeferredWipeout: true
            )
        }
    }
}
