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

        // ============================================================
        // SOURCE
        // ============================================================

        stage('Checkout') {
            steps {
                checkout scm

                sh '''
                    set -e

                    echo "======================================"
                    echo " Mini-SOAR CI/CD Pipeline"
                    echo "======================================"

                    echo ""
                    echo "Commit:"
                    git rev-parse --short HEAD

                    echo ""
                    echo "Build:"
                    echo "${BUILD_NUMBER}"

                    echo ""
                    echo "Workspace:"
                    pwd
                '''
            }
        }


        // ============================================================
        // ENVIRONMENT CHECK
        // ============================================================

        stage('Environment Check') {
            steps {
                sh '''
                    set -e

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

                    echo "========== Docker Compose =========="
                    docker compose version
                '''
            }
        }


        // ============================================================
        // BACKEND CI
        // ============================================================

        stage('Backend Dependencies') {
            steps {
                sh '''
                    set -e

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
                    set -e

                    . .jenkins-venv/bin/activate

                    echo "Running Python compile validation..."

                    python -m compileall src app

                    echo ""
                    echo "Checking Python dependencies..."

                    python -m pip check

                    echo ""
                    echo "Backend validation PASS"
                '''
            }
        }


        // ============================================================
        // FRONTEND CI
        // ============================================================

        stage('Frontend Dependencies') {
            steps {
                dir('frontend') {
                    sh '''
                        set -e

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
                        set -e

                        echo "Building React dashboard..."

                        npm run build

                        echo ""
                        echo "Frontend build PASS"
                    '''
                }
            }
        }


        // ============================================================
        // BUILD DOCKER IMAGES
        // ============================================================

        stage('Build Docker Images') {
            steps {
                sh '''
                    set -e

                    echo "======================================"
                    echo " Building Docker Images"
                    echo "======================================"

                    echo ""
                    echo "Building demo-web..."

                    docker build \
                        -f docker/demo-web.Dockerfile \
                        -t "${DEMO_WEB_IMAGE}" \
                        .

                    echo ""
                    echo "Building Mini-SOAR API..."

                    docker build \
                        -f docker/mini-soar.Dockerfile \
                        -t "${MINI_SOAR_API_IMAGE}" \
                        .

                    echo ""
                    echo "Building dashboard..."

                    docker build \
                        -f frontend/Dockerfile \
                        -t "${DASHBOARD_IMAGE}" \
                        frontend/

                    echo ""
                    echo "Built Docker images:"

                    docker image inspect \
                        "${DEMO_WEB_IMAGE}" \
                        "${MINI_SOAR_API_IMAGE}" \
                        "${DASHBOARD_IMAGE}" \
                        --format '{{.RepoTags}} -> {{.Id}}'
                '''
            }
        }


        // ============================================================
        // VALIDATE CI COMPOSE
        // ============================================================

        stage('Validate CI Compose') {
            steps {
                sh '''
                    set -e

                    docker compose \
                        -f docker-compose.ci.yml \
                        config \
                        >/dev/null

                    echo "docker-compose.ci.yml validation PASS"
                '''
            }
        }


        // ============================================================
        // START CI STACK
        // ============================================================

        stage('Start CI Stack') {
            steps {
                sh '''
                    set -e

                    echo "======================================"
                    echo " Starting CI Stack"
                    echo "======================================"

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


        // ============================================================
        // WAIT FOR SERVICES
        // ============================================================

        stage('Wait For Services') {
            steps {
                sh '''
                    set -e

                    echo "======================================"
                    echo " Waiting for demo-web"
                    echo "======================================"

                    demo_ok=0

                    for attempt in $(seq 1 30)
                    do
                        echo "demo-web attempt ${attempt}/30"

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
                            logs demo-web || true

                        exit 1
                    fi


                    echo ""
                    echo "======================================"
                    echo " Waiting for Mini-SOAR API"
                    echo "======================================"

                    api_ok=0

                    for attempt in $(seq 1 30)
                    do
                        echo "API attempt ${attempt}/30"

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
                            logs mini-soar-api || true

                        exit 1
                    fi


                    echo ""
                    echo "======================================"
                    echo " Waiting for Dashboard"
                    echo "======================================"

                    dashboard_ok=0

                    for attempt in $(seq 1 30)
                    do
                        echo "Dashboard attempt ${attempt}/30"

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
                            logs mini-soar-dashboard || true

                        exit 1
                    fi

                    echo ""
                    echo "All CI services are reachable."
                '''
            }
        }


        // ============================================================
        // API SMOKE TESTS
        // ============================================================

        stage('API Smoke Tests') {
            steps {
                sh '''
                    set -e

                    echo "======================================"
                    echo " API Smoke Tests"
                    echo "======================================"

                    echo ""
                    echo "Testing OpenAPI..."

                    curl \
                        --fail \
                        --silent \
                        http://127.0.0.1:19000/openapi.json \
                        >/dev/null

                    echo "OpenAPI PASS"


                    echo ""
                    echo "Testing MariaDB integration..."

                    curl \
                        --fail \
                        --silent \
                        http://127.0.0.1:19000/api/v1/remediations/summary

                    echo ""
                    echo "MariaDB integration PASS"


                    echo ""
                    echo "Testing dashboard reverse proxy..."

                    curl \
                        --fail \
                        --silent \
                        http://127.0.0.1:18080/api/v1/remediations/summary

                    echo ""
                    echo "Dashboard reverse proxy PASS"

                    echo ""
                    echo "API smoke tests PASS"
                '''
            }
        }


        // ============================================================
        // DOCKER CONTROL PLANE
        // ============================================================

        stage('Docker Control Plane Check') {
            steps {
                sh '''
                    set -e

                    echo "======================================"
                    echo " Docker Control Plane Compatibility"
                    echo "======================================"

                    API_CONTAINER="$(
                        docker compose \
                            -f docker-compose.ci.yml \
                            ps -q mini-soar-api
                    )"

                    if [ -z "${API_CONTAINER}" ]
                    then
                        echo "Mini-SOAR API container not found"
                        exit 1
                    fi

                    echo ""
                    echo "Mini-SOAR API container:"
                    echo "${API_CONTAINER}"

                    echo ""
                    echo "Docker client/server compatibility:"

                    docker exec \
                        "${API_CONTAINER}" \
                        docker version

                    echo ""
                    echo "Verifying demo-web visibility:"

                    docker exec \
                        "${API_CONTAINER}" \
                        docker inspect demo-web \
                        --format 'running={{.State.Running}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}'

                    echo ""
                    echo "Docker control plane check PASS"
                '''
            }
        }


        // ============================================================
        // SELF-HEALING TEST
        // ============================================================

        stage('Self-Healing Smoke Test') {
            steps {
                sh '''
                    set -e

                    echo "======================================"
                    echo " Mini-SOAR Self-Healing Smoke Test"
                    echo "======================================"

                    echo ""
                    echo "Stopping demo-web..."

                    docker stop demo-web

                    echo ""
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
                        echo ""
                        echo "Self-healing smoke test FAILED"

                        echo ""
                        echo "========== Mini-SOAR API logs =========="

                        docker compose \
                            -f docker-compose.ci.yml \
                            logs mini-soar-api || true

                        echo ""
                        echo "========== demo-web logs =========="

                        docker logs demo-web || true

                        exit 1
                    fi

                    echo ""
                    echo "demo-web recovered successfully."
                    echo "Self-healing smoke test PASS"
                '''
            }
        }


        // ============================================================
        // AUDIT VERIFICATION
        // ============================================================

        stage('Verify Audit Persistence') {
            steps {
                sh '''
                    set -e

                    echo "======================================"
                    echo " Verify Audit Persistence"
                    echo "======================================"

                    echo ""
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


        // ============================================================
        // PACKAGE TESTED ARTIFACTS
        // ============================================================

        stage('Package Deployment Artifacts') {
            steps {
                sh '''
                    set -e

                    echo "======================================"
                    echo " Packaging Tested Docker Images"
                    echo "======================================"

                    rm -rf deploy-artifacts
                    mkdir -p deploy-artifacts

                    echo ""
                    echo "Saving:"
                    echo "  ${DEMO_WEB_IMAGE}"
                    echo "  ${MINI_SOAR_API_IMAGE}"
                    echo "  ${DASHBOARD_IMAGE}"

                    docker save \
                        "${DEMO_WEB_IMAGE}" \
                        "${MINI_SOAR_API_IMAGE}" \
                        "${DASHBOARD_IMAGE}" \
                        | gzip > deploy-artifacts/mini-soar-images.tar.gz

                    cp \
                        docker-compose.yml \
                        deploy-artifacts/docker-compose.yml

                    printf '%s\n' \
                        "DEMO_WEB_IMAGE=${DEMO_WEB_IMAGE}" \
                        "MINI_SOAR_API_IMAGE=${MINI_SOAR_API_IMAGE}" \
                        "DASHBOARD_IMAGE=${DASHBOARD_IMAGE}" \
                        > deploy-artifacts/.deploy.env

                    echo ""
                    echo "Deployment artifacts:"

                    ls -lah deploy-artifacts/

                    echo ""
                    echo "Deployment image versions:"

                    cat deploy-artifacts/.deploy.env

                    echo ""
                    echo "Artifact packaging PASS"
                '''
            }
        }


        // ============================================================
        // TRANSFER TO LAB SERVER
        // ============================================================

        stage('Transfer Deployment Artifacts') {
            steps {
                sshagent(credentials: ['mini-soar-deploy-ssh']) {
                    sh '''
                        set -e

                        DEPLOY_HOST="192.168.136.110"
                        DEPLOY_USER="mini-soar-deploy"
                        DEPLOY_DIR="/opt/mini-soar"

                        echo "======================================"
                        echo " Transfer Deployment Artifacts"
                        echo "======================================"

                        echo ""
                        echo "Checking SSH connectivity..."

                        ssh \
                            -o BatchMode=yes \
                            -o StrictHostKeyChecking=yes \
                            -o ConnectTimeout=10 \
                            -o ConnectionAttempts=2 \
                            "${DEPLOY_USER}@${DEPLOY_HOST}" \
                            "mkdir -p ${DEPLOY_DIR}"

                        echo "SSH connectivity PASS"

                        echo ""
                        echo "Transferring deployment artifacts..."

                        scp \
                            -o BatchMode=yes \
                            -o StrictHostKeyChecking=yes \
                            -o ConnectTimeout=10 \
                            -o ConnectionAttempts=2 \
                            deploy-artifacts/mini-soar-images.tar.gz \
                            deploy-artifacts/docker-compose.yml \
                            deploy-artifacts/.deploy.env \
                            "${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_DIR}/"

                        echo ""
                        echo "Artifact transfer PASS"
                    '''
                }
            }
        }


        // ============================================================
        // DEPLOY
        // ============================================================

        stage('Deploy to Lab Server') {
            steps {
                sshagent(credentials: ['mini-soar-deploy-ssh']) {
                    sh '''
                        set -e

                        DEPLOY_HOST="192.168.136.110"
                        DEPLOY_USER="mini-soar-deploy"
                        DEPLOY_DIR="/opt/mini-soar"

                        echo "======================================"
                        echo " Deploying Mini-SOAR"
                        echo "======================================"

                        ssh \
                            -o BatchMode=yes \
                            -o StrictHostKeyChecking=yes \
                            -o ConnectTimeout=10 \
                            -o ConnectionAttempts=2 \
                            "${DEPLOY_USER}@${DEPLOY_HOST}" \
                            "
                                set -e

                                cd ${DEPLOY_DIR}

                                echo 'Checking deployment files...'

                                test -f .env
                                test -f .deploy.env
                                test -f docker-compose.yml
                                test -f mini-soar-images.tar.gz

                                echo 'Deployment files OK'

                                echo ''
                                echo 'Docker version:'
                                docker --version

                                echo ''
                                echo 'Docker Compose version:'
                                docker compose version

                                echo ''
                                echo 'Validating image archive...'
                                gzip -t mini-soar-images.tar.gz

                                echo ''
                                echo 'Loading tested Docker images...'

                                gzip -dc mini-soar-images.tar.gz \
                                    | docker load

                                echo ''
                                echo 'Images loaded.'

                                echo ''
                                echo 'Validating production Compose configuration...'

                                docker compose \
                                    --env-file .deploy.env \
                                    -f docker-compose.yml \
                                    config \
                                    >/dev/null

                                echo 'Compose validation PASS'

                                echo ''
                                echo 'Starting application stack...'

                                docker compose \
                                    --env-file .deploy.env \
                                    -f docker-compose.yml \
                                    up -d \
                                    --no-build

                                echo ''
                                echo 'Current stack:'

                                docker compose \
                                    --env-file .deploy.env \
                                    -f docker-compose.yml \
                                    ps

                                echo ''
                                echo 'Deployment command completed.'
                            "

                        echo ""
                        echo "Compose deployment PASS"
                    '''
                }
            }
        }


        // ============================================================
        // PHASE 7.5 - POST-DEPLOYMENT VERIFICATION
        // ============================================================

        stage('Post-Deployment Verification') {
            steps {
                sshagent(credentials: ['mini-soar-deploy-ssh']) {
                    sh '''
                        set -e

                        DEPLOY_HOST="192.168.136.110"
                        DEPLOY_USER="mini-soar-deploy"

                        echo "======================================"
                        echo " Post-Deployment Verification"
                        echo "======================================"

                        # ------------------------------------------------
                        # demo-web
                        # ------------------------------------------------

                        echo ""
                        echo "Waiting for demo-web..."

                        demo_ok=0

                        for attempt in $(seq 1 30)
                        do
                            echo "demo-web attempt ${attempt}/30"

                            if curl \
                                --fail \
                                --silent \
                                --show-error \
                                http://${DEPLOY_HOST}:8000/health \
                                >/dev/null
                            then
                                demo_ok=1
                                break
                            fi

                            sleep 2
                        done

                        if [ "${demo_ok}" -ne 1 ]
                        then
                            echo ""
                            echo "demo-web post-deployment health check FAILED"

                            ssh \
                                -o BatchMode=yes \
                                -o StrictHostKeyChecking=yes \
                                -o ConnectTimeout=10 \
                                "${DEPLOY_USER}@${DEPLOY_HOST}" \
                                "docker logs --tail 100 demo-web" \
                                || true

                            exit 1
                        fi

                        echo "demo-web health PASS"


                        # ------------------------------------------------
                        # Mini-SOAR API
                        # ------------------------------------------------

                        echo ""
                        echo "Waiting for Mini-SOAR API..."

                        api_ok=0

                        for attempt in $(seq 1 30)
                        do
                            echo "API attempt ${attempt}/30"

                            if curl \
                                --fail \
                                --silent \
                                --show-error \
                                http://${DEPLOY_HOST}:9000/health \
                                >/dev/null
                            then
                                api_ok=1
                                break
                            fi

                            sleep 2
                        done

                        if [ "${api_ok}" -ne 1 ]
                        then
                            echo ""
                            echo "Mini-SOAR API post-deployment health check FAILED"

                            ssh \
                                -o BatchMode=yes \
                                -o StrictHostKeyChecking=yes \
                                -o ConnectTimeout=10 \
                                "${DEPLOY_USER}@${DEPLOY_HOST}" \
                                "docker logs --tail 100 mini-soar-api" \
                                || true

                            exit 1
                        fi

                        echo "Mini-SOAR API health PASS"


                        # ------------------------------------------------
                        # Dashboard
                        # ------------------------------------------------

                        echo ""
                        echo "Waiting for dashboard..."

                        dashboard_ok=0

                        for attempt in $(seq 1 30)
                        do
                            echo "Dashboard attempt ${attempt}/30"

                            if curl \
                                --fail \
                                --silent \
                                --show-error \
                                http://${DEPLOY_HOST}:8080/healthz \
                                >/dev/null
                            then
                                dashboard_ok=1
                                break
                            fi

                            sleep 2
                        done

                        if [ "${dashboard_ok}" -ne 1 ]
                        then
                            echo ""
                            echo "Dashboard post-deployment health check FAILED"

                            ssh \
                                -o BatchMode=yes \
                                -o StrictHostKeyChecking=yes \
                                -o ConnectTimeout=10 \
                                "${DEPLOY_USER}@${DEPLOY_HOST}" \
                                "docker logs --tail 100 mini-soar-dashboard" \
                                || true

                            exit 1
                        fi

                        echo "Dashboard health PASS"


                        # ------------------------------------------------
                        # Dashboard -> API -> MariaDB
                        # ------------------------------------------------

                        echo ""
                        echo "Testing dashboard reverse proxy..."

                        curl \
                            --fail \
                            --silent \
                            --show-error \
                            http://${DEPLOY_HOST}:8080/api/v1/remediations/summary \
                            >/dev/null

                        echo "Dashboard reverse proxy PASS"


                        # ------------------------------------------------
                        # API -> MariaDB
                        # ------------------------------------------------

                        echo ""
                        echo "Testing deployed API database access..."

                        curl \
                            --fail \
                            --silent \
                            --show-error \
                            http://${DEPLOY_HOST}:9000/api/v1/remediations/summary \
                            >/dev/null

                        echo "API database access PASS"


                        # ------------------------------------------------
                        # VERIFY EXACT DEPLOYED IMAGE VERSIONS
                        # ------------------------------------------------

                        echo ""
                        echo "Verifying deployed image versions..."

                        REMOTE_IMAGES="$(
                            ssh \
                                -o BatchMode=yes \
                                -o StrictHostKeyChecking=yes \
                                -o ConnectTimeout=10 \
                                "${DEPLOY_USER}@${DEPLOY_HOST}" \
                                "docker inspect \
                                    --format '{{.Name}}={{.Config.Image}}' \
                                    demo-web \
                                    mini-soar-api \
                                    mini-soar-dashboard"
                        )"

                        echo "${REMOTE_IMAGES}"

                        echo "${REMOTE_IMAGES}" \
                            | grep -q "/demo-web=${DEMO_WEB_IMAGE}"

                        echo "${REMOTE_IMAGES}" \
                            | grep -q "/mini-soar-api=${MINI_SOAR_API_IMAGE}"

                        echo "${REMOTE_IMAGES}" \
                            | grep -q "/mini-soar-dashboard=${DASHBOARD_IMAGE}"

                        echo ""
                        echo "Deployed image versions PASS"


                        # ------------------------------------------------
                        # FINAL REMOTE STATE
                        # ------------------------------------------------

                        echo ""
                        echo "Remote application state:"

                        ssh \
                            -o BatchMode=yes \
                            -o StrictHostKeyChecking=yes \
                            -o ConnectTimeout=10 \
                            "${DEPLOY_USER}@${DEPLOY_HOST}" \
                            "docker ps \
                                --filter name=demo-web \
                                --filter name=mini-soar-api \
                                --filter name=mini-soar-dashboard \
                                --format 'table {{.Names}}\\t{{.Image}}\\t{{.Status}}'"

                        echo ""
                        echo "======================================"
                        echo " Post-deployment verification PASS"
                        echo "======================================"
                    '''
                }
            }
        }


        // ============================================================
        // BUILD SUMMARY
        // ============================================================

        stage('Build Summary') {
            steps {
                sh '''
                    echo ""
                    echo "======================================"
                    echo " Mini-SOAR CI/CD SUCCESS"
                    echo "======================================"

                    echo ""
                    echo "Backend:"
                    echo "  Python compile             PASS"
                    echo "  Dependency validation     PASS"

                    echo ""
                    echo "Frontend:"
                    echo "  npm ci                     PASS"
                    echo "  TypeScript/Vite build      PASS"

                    echo ""
                    echo "Docker Images:"
                    echo "  demo-web                   PASS"
                    echo "  Mini-SOAR API              PASS"
                    echo "  Dashboard                  PASS"

                    echo ""
                    echo "Integration:"
                    echo "  MariaDB                    PASS"
                    echo "  API                        PASS"
                    echo "  Dashboard proxy            PASS"
                    echo "  Docker control plane       PASS"
                    echo "  Self-healing               PASS"
                    echo "  Audit persistence          PASS"

                    echo ""
                    echo "Deployment:"
                    echo "  Artifact packaging         PASS"
                    echo "  SSH transfer               PASS"
                    echo "  Docker image load          PASS"
                    echo "  Compose deployment         PASS"
                    echo "  Post-deploy health         PASS"
                    echo "  Dashboard/API routing      PASS"
                    echo "  Image version verify       PASS"

                    echo ""
                    echo "Images deployed:"
                    echo "  ${DEMO_WEB_IMAGE}"
                    echo "  ${MINI_SOAR_API_IMAGE}"
                    echo "  ${DASHBOARD_IMAGE}"

                    echo ""
                    echo "======================================"
                '''
            }
        }
    }


    // ================================================================
    // CLEANUP
    // ================================================================

    post {
        always {
            sh '''
                echo ""
                echo "======================================"
                echo " Cleaning CI Stack"
                echo "======================================"

                docker compose \
                    -f docker-compose.ci.yml \
                    down \
                    --volumes \
                    --remove-orphans \
                    || true

                rm -rf .jenkins-venv || true
                rm -rf deploy-artifacts || true
            '''

            cleanWs(
                deleteDirs: true,
                disableDeferredWipeout: true
            )
        }

        success {
            echo 'Mini-SOAR full-stack CI/CD pipeline completed successfully.'
        }

        failure {
            echo 'Mini-SOAR CI/CD pipeline FAILED. Check the failed stage above.'
        }
    }
}
