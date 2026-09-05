pipeline {
    agent {
        label 'ci'
    }

    options {
        timestamps()
        disableConcurrentBuilds()

        buildDiscarder(
            logRotator(
                numToKeepStr: '20'
            )
        )
    }
    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
        PYTHONDONTWRITEBYTECODE = '1'
        CI = 'true'

        DEMO_WEB_IMAGE = "mini-soar-demo-web:${BUILD_NUMBER}"
        MINI_SOAR_API_IMAGE = "mini-soar-api:${BUILD_NUMBER}"
        DASHBOARD_IMAGE = "mini-soar-dashboard:${BUILD_NUMBER}"

        COMPOSE_PROJECT_NAME = "mini-soar-ci-${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm

                sh '''
                    echo "======================================"
                    echo " Mini-SOAR CI Pipeline"
                    echo "======================================"

                    echo "Commit:"
                    git rev-parse --short HEAD

                    echo "Build:"
                    echo "${BUILD_NUMBER}"

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

                    echo "========== Docker =========="
                    docker --version

                    echo "========== Compose =========="
                    docker compose version
                '''
            }
        }

        stage('Backend Dependencies') {
            steps {
                sh '''
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
                        npm ci
                    '''
                }
            }
        }

        stage('Frontend Build') {
            steps {
                dir('frontend') {
                    sh '''
                        npm run build
                    '''
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    set -e

                    echo "Building demo-web..."
                    docker build \
                        -f docker/demo-web.Dockerfile \
                        -t "${DEMO_WEB_IMAGE}" \
                        .

                    echo "Building Mini-SOAR API..."
                    docker build \
                        -f docker/mini-soar.Dockerfile \
                        -t "${MINI_SOAR_API_IMAGE}" \
                        .

                    echo "Building dashboard..."
                    docker build \
                        -f frontend/Dockerfile \
                        -t "${DASHBOARD_IMAGE}" \
                        frontend/

                    echo ""
                    echo "Images:"
                    docker image inspect \
                        "${DEMO_WEB_IMAGE}" \
                        "${MINI_SOAR_API_IMAGE}" \
                        "${DASHBOARD_IMAGE}" \
                        --format '{{.RepoTags}} -> {{.Id}}'
                '''
            }
        }

        stage('Validate CI Compose') {
            steps {
                sh '''
                    docker compose \
                        -f docker-compose.ci.yml \
                        config \
                        >/dev/null

                    echo "docker-compose.ci.yml validation PASS"
                '''
            }
        }

        stage('Start CI Stack') {
            steps {
                sh '''
                    set -e

                    docker compose \
                        -f docker-compose.ci.yml \
                        up -d

                    echo ""
                    docker compose \
                        -f docker-compose.ci.yml \
                        ps
                '''
            }
        }

        stage('Wait For Services') {
            steps {
                sh '''
                    set -e

                    echo "Waiting for demo-web..."

                    demo_ok=0

                    for attempt in $(seq 1 30)
                    do
                        if curl \
                            --fail \
                            --silent \
                            http://127.0.0.1:18000/health \
                            >/dev/null
                        then
                            demo_ok=1
                            break
                        fi

                        sleep 2
                    done

                    if [ "${demo_ok}" -ne 1 ]
                    then
                        echo "demo-web did not become healthy"
                        docker compose \
                            -f docker-compose.ci.yml \
                            logs demo-web
                        exit 1
                    fi


                    echo "Waiting for Mini-SOAR API..."

                    api_ok=0

                    for attempt in $(seq 1 30)
                    do
                        if curl \
                            --fail \
                            --silent \
                            http://127.0.0.1:19000/health \
                            >/dev/null
                        then
                            api_ok=1
                            break
                        fi

                        sleep 2
                    done

                    if [ "${api_ok}" -ne 1 ]
                    then
                        echo "Mini-SOAR API did not become healthy"
                        docker compose \
                            -f docker-compose.ci.yml \
                            logs mini-soar-api
                        exit 1
                    fi


                    echo "Waiting for dashboard..."

                    dashboard_ok=0

                    for attempt in $(seq 1 30)
                    do
                        if curl \
                            --fail \
                            --silent \
                            http://127.0.0.1:18080/healthz \
                            >/dev/null
                        then
                            dashboard_ok=1
                            break
                        fi

                        sleep 2
                    done

                    if [ "${dashboard_ok}" -ne 1 ]
                    then
                        echo "Dashboard did not become healthy"
                        docker compose \
                            -f docker-compose.ci.yml \
                            logs mini-soar-dashboard
                        exit 1
                    fi

                    echo "All application services are reachable."
                '''
            }
        }

        stage('API Smoke Tests') {
            steps {
                sh '''
                    set -e

                    echo "Testing API..."

                    curl \
                        --fail \
                        --silent \
                        http://127.0.0.1:19000/openapi.json \
                        >/dev/null

                    echo "Testing MariaDB integration..."

                    curl \
                        --fail \
                        --silent \
                        http://127.0.0.1:19000/api/v1/remediations/summary

                    echo ""

                    echo "Testing dashboard reverse proxy..."

                    curl \
                        --fail \
                        --silent \
                        http://127.0.0.1:18080/api/v1/remediations/summary

                    echo ""

                    echo "API smoke tests PASS"
                '''
            }
        }

        stage('Self-Healing Smoke Test') {
            steps {
                sh '''
                    set -e

                    echo "======================================"
                    echo " Mini-SOAR self-healing smoke test"
                    echo "======================================"

                    echo "Stopping demo-web..."

                    docker stop demo-web

                    echo "Sending synthetic Zabbix DOWN event..."

                    curl \
                      --fail \
                      --silent \
                      --show-error \
                      -X POST \
                      -H 'Content-Type: application/json' \
                      -d '{
                            "source": "zabbix",
                            "event_id": "CI-'${BUILD_NUMBER}'",
                            "event_name": "[CI] demo-web Container down",
                            "event_value": 1,
                            "severity": "High",
                            "host": "jenkins-ci",
                            "trigger_id": "CI-'${BUILD_NUMBER}'",
                            "tags": [
                              {
                                "tag": "event_type",
                                "value": "CONTAINER_DOWN"
                              },
                              {
                                "tag": "service",
                                "value": "demo-web"
                              },
                              {
                                "tag": "managed_by",
                                "value": "mini-soar"
                              }
                            ]
                          }' \
                      http://127.0.0.1:19000/api/v1/webhooks/zabbix

                    echo ""
                    echo "Waiting for Mini-SOAR recovery..."

                    recovered=0

                    for attempt in $(seq 1 60)
                    do
                        running="$(
                            docker inspect \
                              --format '{{.State.Running}}' \
                              demo-web \
                              2>/dev/null || echo false
                        )"

                        health="$(
                            docker inspect \
                              --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' \
                              demo-web \
                              2>/dev/null || echo unknown
                        )"

                        echo \
                          "Attempt ${attempt}/60: " \
                          "running=${running} health=${health}"

                        if [ "${running}" = "true" ] \
                           && [ "${health}" = "healthy" ]
                        then
                            recovered=1
                            break
                        fi

                        sleep 2
                    done

                    if [ "${recovered}" -ne 1 ]
                    then
                        echo "Self-healing smoke test FAILED"

                        echo "========== API logs =========="
                        docker compose \
                          -f docker-compose.ci.yml \
                          logs mini-soar-api || true

                        echo "========== demo-web logs =========="
                        docker logs demo-web || true

                        exit 1
                    fi

                    echo ""
                    echo "demo-web recovered successfully."
                '''
            }
        }

        stage('Verify Audit Persistence') {
            steps {
                sh '''
                    set -e

                    echo "Checking remediation record..."

                    result="$(
                      curl \
                        --fail \
                        --silent \
                        "http://127.0.0.1:19000/api/v1/remediations/CI-${BUILD_NUMBER}"
                    )"

                    echo "${result}"

                    echo "${result}" \
                      | grep -q '"status":"SUCCESS"'

                    echo "${result}" \
                      | grep -q '"action":"start"'

                    echo ""
                    echo "Audit persistence PASS"
                '''
            }
        }

        stage('Build Summary') {
            steps {
                sh '''
                    echo ""
                    echo "======================================"
                    echo " Mini-SOAR CI SUCCESS"
                    echo "======================================"

                    echo ""
                    echo "Backend:"
                    echo "  Python compile          PASS"
                    echo "  Dependency validation  PASS"

                    echo ""
                    echo "Frontend:"
                    echo "  npm ci                  PASS"
                    echo "  TypeScript/Vite build   PASS"

                    echo ""
                    echo "Containers:"
                    echo "  demo-web image          PASS"
                    echo "  Mini-SOAR API image     PASS"
                    echo "  Dashboard image         PASS"

                    echo ""
                    echo "Integration:"
                    echo "  MariaDB                 PASS"
                    echo "  API                     PASS"
                    echo "  Dashboard proxy         PASS"
                    echo "  Docker socket           PASS"
                    echo "  Self-healing            PASS"
                    echo "  Audit persistence       PASS"
                    echo ""
                '''
            }
        }
    }

    post {
        always {
            sh '''
                echo "Cleaning CI stack..."

                docker compose \
                    -f docker-compose.ci.yml \
                    down \
                    --volumes \
                    --remove-orphans \
                    || true

                rm -rf .jenkins-venv || true
            '''

            cleanWs(
                deleteDirs: true,
                disableDeferredWipeout: true
            )
        }

        success {
            echo 'Mini-SOAR full-stack CI completed successfully.'
        }

        failure {
            echo 'Mini-SOAR CI FAILED. Check the failed stage.'
        }
    }
}
