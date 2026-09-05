pipeline {
    agent {
        label 'ci'
    }

    options {
        timestamps()

        // Prevent two deployments from the same job running concurrently.
        disableConcurrentBuilds()

        // We perform checkout explicitly in the Checkout stage.
        skipDefaultCheckout(true)

        // Allow "Restart from Stage" to recover deployment artifacts.
        preserveStashes(
            buildCount: 5
        )

        // Prevent a stuck build from running indefinitely.
        timeout(
            time: 30,
            unit: 'MINUTES'
        )

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

        DEPLOY_HOST = '192.168.136.110'
        DEPLOY_USER = 'mini-soar-deploy'
        DEPLOY_DIR = '/opt/mini-soar'

        // Used by post-failure rollback logic.
        DEPLOY_ATTEMPTED = 'false'
        DEPLOY_VERIFIED = 'false'
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
                    git rev-parse HEAD

                    echo ""
                    echo "Branch:"
                    git branch --show-current || true

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
        // ENVIRONMENT
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

                    echo "========== curl =========="
                    curl --version | head -1

                    echo "========== SSH =========="
                    ssh -V 2>&1
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
                    echo "Checking dependency consistency..."

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

                        npm run build

                        echo ""
                        echo "Frontend build PASS"
                    '''
                }
            }
        }


        // ============================================================
        // BUILD TESTED DOCKER ARTIFACTS
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
                    echo "Built images:"

                    docker image inspect \
                        "${DEMO_WEB_IMAGE}" \
                        "${MINI_SOAR_API_IMAGE}" \
                        "${DASHBOARD_IMAGE}" \
                        --format '{{.RepoTags}} -> {{.Id}}'

                    echo ""
                    echo "Docker image build PASS"
                '''
            }
        }


        // ============================================================
        // CI COMPOSE VALIDATION
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
        // START ISOLATED CI STACK
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
        // SERVICE READINESS
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
        // API INTEGRATION
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
                        http://127.0.0.1:19000/api/v1/remediations/summary \
                        >/dev/null

                    echo "MariaDB integration PASS"


                    echo ""
                    echo "Testing dashboard reverse proxy..."

                    curl \
                        --fail \
                        --silent \
                        http://127.0.0.1:18080/api/v1/remediations/summary \
                        >/dev/null

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
        // SELF-HEALING INTEGRATION TEST
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
        // AUDIT
        // ============================================================

        stage('Verify Audit Persistence') {
            steps {
                sh '''
                    set -e

                    echo "======================================"
                    echo " Verify Audit Persistence"
                    echo "======================================"

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
        // DEPLOYMENT GATE
        // ============================================================

        stage('Deployment Gate') {
            steps {
                sh '''
                    set -e

                    echo "======================================"
                    echo " Deployment Gate"
                    echo "======================================"

                    git fetch origin main --quiet

                    CURRENT_SHA="$(git rev-parse HEAD)"
                    MAIN_SHA="$(git rev-parse origin/main)"

                    echo ""
                    echo "Current commit:"
                    echo "${CURRENT_SHA}"

                    echo ""
                    echo "origin/main:"
                    echo "${MAIN_SHA}"

                    if [ "${CURRENT_SHA}" != "${MAIN_SHA}" ]
                    then
                        echo ""
                        echo "DEPLOYMENT BLOCKED"
                        echo "The tested commit is not origin/main."

                        exit 1
                    fi

                    echo ""
                    echo "Deployment gate PASS"
                '''
            }
        }


        // ============================================================
        // PACKAGE + CHECKSUM + METADATA
        // ============================================================

        stage('Package Deployment Artifacts') {
            steps {
                sh '''
                    set -e

                    echo "======================================"
                    echo " Packaging Tested Artifacts"
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
                        | gzip \
                        > deploy-artifacts/mini-soar-images.tar.gz

                    cp \
                        docker-compose.yml \
                        deploy-artifacts/docker-compose.yml

                    printf '%s\n' \
                        "DEMO_WEB_IMAGE=${DEMO_WEB_IMAGE}" \
                        "MINI_SOAR_API_IMAGE=${MINI_SOAR_API_IMAGE}" \
                        "DASHBOARD_IMAGE=${DASHBOARD_IMAGE}" \
                        > deploy-artifacts/.deploy.env

                    (
                        cd deploy-artifacts

                        sha256sum \
                            mini-soar-images.tar.gz \
                            > mini-soar-images.tar.gz.sha256
                    )

                    COMMIT_SHA="$(git rev-parse HEAD)"
                    DEPLOYED_AT="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

                    ARCHIVE_SHA256="$(
                        awk '{print $1}' \
                            deploy-artifacts/mini-soar-images.tar.gz.sha256
                    )"

                    printf '%s\n' \
                        "BUILD_NUMBER=${BUILD_NUMBER}" \
                        "COMMIT_SHA=${COMMIT_SHA}" \
                        "CREATED_AT=${DEPLOYED_AT}" \
                        "ARCHIVE_SHA256=${ARCHIVE_SHA256}" \
                        "DEMO_WEB_IMAGE=${DEMO_WEB_IMAGE}" \
                        "MINI_SOAR_API_IMAGE=${MINI_SOAR_API_IMAGE}" \
                        "DASHBOARD_IMAGE=${DASHBOARD_IMAGE}" \
                        > deploy-artifacts/deployment.env

                    echo ""
                    echo "Deployment artifacts:"

                    ls -lah deploy-artifacts/

                    echo ""
                    echo "Deployment metadata:"

                    cat deploy-artifacts/deployment.env

                    echo ""
                    echo "Artifact checksum:"

                    cat deploy-artifacts/mini-soar-images.tar.gz.sha256

                    echo ""
                    echo "Artifact packaging PASS"
                '''

                // Allows restart from Transfer Deployment Artifacts.
                stash(
                    name: 'deployment-artifacts',
                    includes: 'deploy-artifacts/**,deploy-artifacts/.deploy.env',
                    useDefaultExcludes: false
                )

                // Safe metadata only — no secrets.
                archiveArtifacts(
                    artifacts: 'deploy-artifacts/deployment.env',
                    fingerprint: true
                )
            }
        }


        // ============================================================
        // BACKUP CURRENT RELEASE + TRANSFER
        // ============================================================

        stage('Transfer Deployment Artifacts') {
            steps {
                // Restores artifacts automatically when restarting this stage.
                unstash 'deployment-artifacts'

                sshagent(credentials: ['mini-soar-deploy-ssh']) {
                    sh '''
                        set -e

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
                        echo "Backing up current deployment metadata..."

                        ssh \
                            -o BatchMode=yes \
                            -o StrictHostKeyChecking=yes \
                            -o ConnectTimeout=10 \
                            -o ConnectionAttempts=2 \
                            "${DEPLOY_USER}@${DEPLOY_HOST}" \
                            "
                                set -e

                                cd ${DEPLOY_DIR}

                                if [ -f .deploy.env ]
                                then
                                    cp .deploy.env .deploy.env.previous
                                fi

                                if [ -f docker-compose.yml ]
                                then
                                    cp docker-compose.yml docker-compose.previous.yml
                                fi

                                if [ -f deployment.env ]
                                then
                                    cp deployment.env deployment.previous.env
                                fi
                            "

                        echo "Previous deployment metadata backup PASS"


                        echo ""
                        echo "Transferring deployment artifacts..."

                        scp \
                            -o BatchMode=yes \
                            -o StrictHostKeyChecking=yes \
                            -o ConnectTimeout=10 \
                            -o ConnectionAttempts=2 \
                            deploy-artifacts/mini-soar-images.tar.gz \
                            deploy-artifacts/mini-soar-images.tar.gz.sha256 \
                            deploy-artifacts/docker-compose.yml \
                            deploy-artifacts/.deploy.env \
                            deploy-artifacts/deployment.env \
                            "${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_DIR}/"

                        echo ""
                        echo "Artifact transfer PASS"
                    '''
                }
            }
        }


        // ============================================================
        // DEPLOY TESTED ARTIFACT
        // ============================================================

        stage('Deploy to Lab Server') {
            steps {
                script {
                    env.DEPLOY_ATTEMPTED = 'true'
                }

                sshagent(credentials: ['mini-soar-deploy-ssh']) {
                    sh '''
                        set -e

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
                                test -f deployment.env
                                test -f docker-compose.yml
                                test -f mini-soar-images.tar.gz
                                test -f mini-soar-images.tar.gz.sha256

                                echo 'Deployment files OK'


                                echo ''
                                echo 'Verifying artifact checksum...'

                                sha256sum \
                                    -c mini-soar-images.tar.gz.sha256

                                echo 'Artifact checksum PASS'


                                echo ''
                                echo 'Loading tested Docker images...'

                                gzip -dc mini-soar-images.tar.gz \
                                    | docker load

                                echo ''
                                echo 'Docker images loaded.'


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
        // POST-DEPLOY VERIFICATION
        // ============================================================

        stage('Post-Deployment Verification') {
            steps {
                sshagent(credentials: ['mini-soar-deploy-ssh']) {
                    sh '''
                        set -e

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
                            echo "demo-web health check FAILED"

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
                            echo "Mini-SOAR API health check FAILED"

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
                            echo "Dashboard health check FAILED"

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
                        # Direct API -> MariaDB
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
                        # Exact image version verification
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
                            | grep -Fxq "/demo-web=${DEMO_WEB_IMAGE}"

                        echo "${REMOTE_IMAGES}" \
                            | grep -Fxq "/mini-soar-api=${MINI_SOAR_API_IMAGE}"

                        echo "${REMOTE_IMAGES}" \
                            | grep -Fxq "/mini-soar-dashboard=${DASHBOARD_IMAGE}"

                        echo "Deployed image versions PASS"


                        # ------------------------------------------------
                        # Deployment metadata verification
                        # ------------------------------------------------

                        echo ""
                        echo "Verifying deployment metadata..."

                        ssh \
                            -o BatchMode=yes \
                            -o StrictHostKeyChecking=yes \
                            -o ConnectTimeout=10 \
                            "${DEPLOY_USER}@${DEPLOY_HOST}" \
                            "grep -Fx 'BUILD_NUMBER=${BUILD_NUMBER}' \
                                ${DEPLOY_DIR}/deployment.env"

                        echo "Deployment metadata PASS"


                        # ------------------------------------------------
                        # Remote state evidence
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

                script {
                    env.DEPLOY_VERIFIED = 'true'
                }
            }
        }


        // ============================================================
        // SUCCESSFUL DEPLOYMENT CLEANUP
        // ============================================================

        stage('Finalize Deployment') {
            steps {
                sshagent(credentials: ['mini-soar-deploy-ssh']) {
                    sh '''
                        set +e

                        echo "======================================"
                        echo " Finalizing Deployment"
                        echo "======================================"

                        ssh \
                            -o BatchMode=yes \
                            -o StrictHostKeyChecking=yes \
                            -o ConnectTimeout=10 \
                            "${DEPLOY_USER}@${DEPLOY_HOST}" \
                            "
                                cd ${DEPLOY_DIR} || exit 0

                                echo 'Removing transferred image archive...'

                                rm -f \
                                    mini-soar-images.tar.gz \
                                    mini-soar-images.tar.gz.sha256

                                echo 'Cleaning dangling Docker images...'

                                docker image prune -f || true
                            "

                        echo ""
                        echo "Deployment cleanup completed."
                    '''
                }
            }
        }


        // ============================================================
        // SUMMARY
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
                    echo "Docker:"
                    echo "  demo-web image             PASS"
                    echo "  Mini-SOAR API image        PASS"
                    echo "  Dashboard image            PASS"
                    echo "  Docker control plane       PASS"

                    echo ""
                    echo "Integration:"
                    echo "  MariaDB                    PASS"
                    echo "  API                        PASS"
                    echo "  Dashboard reverse proxy    PASS"
                    echo "  Self-healing               PASS"
                    echo "  Audit persistence          PASS"

                    echo ""
                    echo "Security / Hardening:"
                    echo "  Main deployment gate       PASS"
                    echo "  Artifact SHA256            PASS"
                    echo "  Deployment metadata        PASS"
                    echo "  SSH host verification      PASS"

                    echo ""
                    echo "Deployment:"
                    echo "  Artifact packaging         PASS"
                    echo "  Artifact stash             PASS"
                    echo "  SSH/SCP transfer           PASS"
                    echo "  Docker image load          PASS"
                    echo "  Compose deployment         PASS"
                    echo "  Post-deploy health         PASS"
                    echo "  Image version verify       PASS"

                    echo ""
                    echo "Build:"
                    echo "  ${BUILD_NUMBER}"

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
    // POST ACTIONS
    // ================================================================

    post {

        // ------------------------------------------------------------
        // Automatic rollback
        // ------------------------------------------------------------

        failure {
            script {
                if (
                    env.DEPLOY_ATTEMPTED == 'true' &&
                    env.DEPLOY_VERIFIED != 'true'
                ) {
                    echo 'Deployment failure detected. Attempting rollback...'

                    sshagent(credentials: ['mini-soar-deploy-ssh']) {
                        sh '''
                            set +e

                            echo "======================================"
                            echo " Automatic Rollback"
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

                                    if [ ! -f .deploy.env.previous ] || \
                                       [ ! -f docker-compose.previous.yml ]
                                    then
                                        echo 'Rollback unavailable:'
                                        echo 'No previous deployment metadata exists.'
                                        exit 2
                                    fi

                                    echo ''
                                    echo 'Previous release:'

                                    cat .deploy.env.previous

                                    echo ''
                                    echo 'Restoring previous Docker Compose configuration...'

                                    docker compose \
                                        --env-file .deploy.env.previous \
                                        -f docker-compose.previous.yml \
                                        up -d \
                                        --no-build

                                    cp \
                                        .deploy.env.previous \
                                        .deploy.env

                                    cp \
                                        docker-compose.previous.yml \
                                        docker-compose.yml

                                    if [ -f deployment.previous.env ]
                                    then
                                        cp \
                                            deployment.previous.env \
                                            deployment.env
                                    fi

                                    echo ''
                                    echo 'Waiting briefly for rollback services...'

                                    sleep 10

                                    echo ''
                                    echo 'Rollback stack:'

                                    docker compose \
                                        --env-file .deploy.env \
                                        -f docker-compose.yml \
                                        ps

                                    echo ''
                                    echo 'ROLLBACK COMPLETED'
                                "

                            ROLLBACK_RC=$?

                            if [ "${ROLLBACK_RC}" -eq 0 ]
                            then
                                echo ""
                                echo "Automatic rollback completed successfully."
                            else
                                echo ""
                                echo "WARNING: automatic rollback failed."
                                echo "Rollback exit code: ${ROLLBACK_RC}"
                                echo "Manual recovery may be required."
                            fi

                            // Preserve original pipeline failure.
                            exit 0
                        '''
                    }
                } else {
                    echo 'Rollback not required.'
                    echo "DEPLOY_ATTEMPTED=${env.DEPLOY_ATTEMPTED}"
                    echo "DEPLOY_VERIFIED=${env.DEPLOY_VERIFIED}"
                }
            }

            echo 'Mini-SOAR CI/CD pipeline FAILED. Check the failed stage above.'
        }


        // ------------------------------------------------------------
        // Jenkins CI cleanup
        // ------------------------------------------------------------

        always {
            sh '''
                set +e

                echo ""
                echo "======================================"
                echo " Cleaning Jenkins CI Environment"
                echo "======================================"

                echo ""
                echo "Stopping isolated CI stack..."

                docker compose \
                    -f docker-compose.ci.yml \
                    down \
                    --volumes \
                    --remove-orphans \
                    || true


                echo ""
                echo "Removing build-specific CI images..."

                docker image rm \
                    "${DEMO_WEB_IMAGE}" \
                    "${MINI_SOAR_API_IMAGE}" \
                    "${DASHBOARD_IMAGE}" \
                    2>/dev/null \
                    || true


                echo ""
                echo "Removing dangling images..."

                docker image prune -f || true


                echo ""
                echo "Removing Docker builder cache older than 7 days..."

                docker builder prune \
                    -f \
                    --filter 'until=168h' \
                    || true


                echo ""
                echo "Removing temporary files..."

                rm -rf .jenkins-venv || true
                rm -rf deploy-artifacts || true


                echo ""
                echo "Jenkins cleanup completed."
            '''

            cleanWs(
                deleteDirs: true,
                disableDeferredWipeout: true
            )
        }


        success {
            echo 'Mini-SOAR full-stack CI/CD pipeline completed successfully.'
        }
    }
}
