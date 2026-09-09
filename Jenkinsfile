pipeline {
    agent {
        label 'ci'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
        skipDefaultCheckout(true)

        preserveStashes(
            buildCount: 5
        )

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

        DEPLOY_ATTEMPTED = 'false'
        DEPLOY_VERIFIED = 'false'
    }

    stages {

        // ============================================================
        // 1. CHECK
        // ============================================================

        stage('Check') {
            steps {

                // ----------------------------------------------------
                // Checkout
                // ----------------------------------------------------

                checkout scm

                sh '''
                    set -e

                    echo "======================================"
                    echo " Mini-SOAR - CHECK"
                    echo "======================================"

                    echo "Commit : $(git rev-parse HEAD)"
                    echo "Branch : $(git branch --show-current || true)"
                    echo "Build  : ${BUILD_NUMBER}"
                    echo "Path   : $(pwd)"
                '''


                // ----------------------------------------------------
                // Environment
                // ----------------------------------------------------

                sh '''
                    set -e

                    echo ""
                    echo "========== Environment =========="

                    python3 --version
                    python3 -m pip --version

                    node --version
                    npm --version

                    docker --version
                    docker compose version

                    curl --version | head -1
                    ssh -V 2>&1
                '''


                // ----------------------------------------------------
                // Backend
                // ----------------------------------------------------

                sh '''
                    set -e

                    echo ""
                    echo "========== Backend =========="

                    rm -rf .jenkins-venv

                    python3 -m venv .jenkins-venv

                    . .jenkins-venv/bin/activate

                    python -m pip install --upgrade pip

                    python -m pip install \
                        -r requirements.txt

                    python -m compileall src app

                    python -m pip check

                    echo "Backend validation PASS"
                '''


                // ----------------------------------------------------
                // Frontend
                // ----------------------------------------------------

                dir('frontend') {
                    sh '''
                        set -e

                        echo ""
                        echo "========== Frontend =========="

                        npm ci
                        npm run build

                        echo "Frontend validation PASS"
                    '''
                }


                // ----------------------------------------------------
                // Compose validation
                // ----------------------------------------------------

                sh '''
                    set -e

                    echo ""
                    echo "========== CI Compose =========="

                    docker compose \
                        -f docker-compose.ci.yml \
                        config \
                        >/dev/null

                    echo "CI Compose validation PASS"

                    echo ""
                    echo "======================================"
                    echo " CHECK PASS"
                    echo "======================================"
                '''
            }
        }


        // ============================================================
        // 2. BUILD & TEST
        // ============================================================

        stage('Build & Test') {
            steps {

                // ----------------------------------------------------
                // Build Docker images
                // ----------------------------------------------------

                sh '''
                    set -e

                    echo "======================================"
                    echo " Mini-SOAR - BUILD & TEST"
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


                // ----------------------------------------------------
                // Start CI stack + readiness
                // ----------------------------------------------------

                sh '''
                    set -e

                    echo ""
                    echo "========== Starting CI Stack =========="

                    docker compose \
                        -f docker-compose.ci.yml \
                        up -d

                    docker compose \
                        -f docker-compose.ci.yml \
                        ps


                    wait_http() {
                        NAME="$1"
                        URL="$2"
                        SERVICE="$3"
                        ATTEMPTS="${4:-30}"

                        for attempt in $(seq 1 "$ATTEMPTS")
                        do
                            if curl \
                                --fail \
                                --silent \
                                "$URL" \
                                >/dev/null
                            then
                                echo "[PASS] ${NAME}"
                                return 0
                            fi

                            echo \
                                "[${attempt}/${ATTEMPTS}] Waiting for ${NAME}..."

                            sleep 2
                        done

                        echo "[FAIL] ${NAME}"

                        if [ -n "$SERVICE" ]
                        then
                            docker compose \
                                -f docker-compose.ci.yml \
                                logs "$SERVICE" \
                                || true
                        fi

                        return 1
                    }


                    echo ""
                    echo "========== Service Readiness =========="

                    wait_http \
                        "demo-web" \
                        "http://127.0.0.1:18000/health" \
                        "demo-web"

                    wait_http \
                        "Mini-SOAR API" \
                        "http://127.0.0.1:19000/health" \
                        "mini-soar-api"

                    wait_http \
                        "Dashboard" \
                        "http://127.0.0.1:18080/healthz" \
                        "mini-soar-dashboard"

                    echo ""
                    echo "All CI services ready."
                '''


                // ----------------------------------------------------
                // API + integration tests
                // ----------------------------------------------------

                sh '''
                    set -e

                    echo ""
                    echo "========== API Smoke Tests =========="

                    curl \
                        --fail \
                        --silent \
                        http://127.0.0.1:19000/openapi.json \
                        >/dev/null

                    echo "OpenAPI PASS"


                    curl \
                        --fail \
                        --silent \
                        http://127.0.0.1:19000/api/v1/remediations/summary \
                        >/dev/null

                    echo "MariaDB integration PASS"


                    curl \
                        --fail \
                        --silent \
                        http://127.0.0.1:18080/api/v1/remediations/summary \
                        >/dev/null

                    echo "Dashboard reverse proxy PASS"
                '''


                // ----------------------------------------------------
                // Docker control plane
                // ----------------------------------------------------

                sh '''
                    set -e

                    echo ""
                    echo "========== Docker Control Plane =========="

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


                    echo "Docker client/server compatibility:"

                    docker exec \
                        "${API_CONTAINER}" \
                        docker version


                    echo ""
                    echo "demo-web visibility:"

                    docker exec \
                        "${API_CONTAINER}" \
                        docker inspect demo-web \
                        --format \
                        'running={{.State.Running}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}'

                    echo ""
                    echo "Docker control plane PASS"
                '''


                // ----------------------------------------------------
                // Self-healing integration test
                // ----------------------------------------------------

                sh '''
                    set -e

                    echo ""
                    echo "========== Self-Healing Test =========="

                    EVENT_ID="CI-${BUILD_NUMBER}"

                    echo "Stopping demo-web..."

                    docker stop demo-web


                    echo ""
                    echo "Sending synthetic Zabbix event..."

                    PAYLOAD="$(
                        cat <<EOF
{
  "source": "zabbix",
  "event_id": "${EVENT_ID}",
  "event_name": "[CI] demo-web Container down",
  "event_value": 1,
  "severity": "High",
  "host": "jenkins-ci",
  "trigger_id": "${EVENT_ID}",
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
}
EOF
                    )"


                    curl \
                        --fail \
                        --silent \
                        --show-error \
                        -X POST \
                        -H 'Content-Type: application/json' \
                        --data "${PAYLOAD}" \
                        http://127.0.0.1:19000/api/v1/webhooks/zabbix


                    echo ""
                    echo "Waiting for recovery..."

                    recovered=0

                    for attempt in $(seq 1 60)
                    do
                        running="$(
                            docker inspect \
                                --format '{{.State.Running}}' \
                                demo-web \
                                2>/dev/null \
                                || echo false
                        )"

                        health="$(
                            docker inspect \
                                --format \
                                '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' \
                                demo-web \
                                2>/dev/null \
                                || echo unknown
                        )"

                        echo \
                            "Attempt ${attempt}/60: " \
                            "running=${running} health=${health}"

                        if [ "${running}" = "true" ] && \
                           [ "${health}" = "healthy" ]
                        then
                            recovered=1
                            break
                        fi

                        sleep 2
                    done


                    if [ "${recovered}" -ne 1 ]
                    then
                        echo ""
                        echo "Self-healing FAILED"

                        echo ""
                        echo "========== Mini-SOAR logs =========="

                        docker compose \
                            -f docker-compose.ci.yml \
                            logs mini-soar-api \
                            || true

                        echo ""
                        echo "========== demo-web logs =========="

                        docker logs demo-web || true

                        exit 1
                    fi


                    echo ""
                    echo "demo-web recovered."

                    echo ""
                    echo "Verifying audit record..."


                    RESULT="$(
                        curl \
                            --fail \
                            --silent \
                            "http://127.0.0.1:19000/api/v1/remediations/${EVENT_ID}"
                    )"

                    echo "${RESULT}"


                    echo "${RESULT}" \
                        | grep -q '"status":"SUCCESS"'

                    echo "${RESULT}" \
                        | grep -q '"action":"start"'

                    echo ""
                    echo "Self-healing + audit verification PASS"
                '''


                // ----------------------------------------------------
                // Deployment Gate
                // ----------------------------------------------------

                sh '''
                    set -e

                    echo ""
                    echo "========== Deployment Gate =========="

                    git fetch origin main --quiet

                    CURRENT_SHA="$(git rev-parse HEAD)"
                    MAIN_SHA="$(git rev-parse origin/main)"

                    echo "Current     : ${CURRENT_SHA}"
                    echo "origin/main : ${MAIN_SHA}"

                    if [ "${CURRENT_SHA}" != "${MAIN_SHA}" ]
                    then
                        echo ""
                        echo "DEPLOYMENT BLOCKED"
                        echo "Tested commit is not origin/main."

                        exit 1
                    fi

                    echo ""
                    echo "Deployment gate PASS"
                '''


                // ----------------------------------------------------
                // Package tested images
                // ----------------------------------------------------

                sh '''
                    set -e

                    echo ""
                    echo "========== Package Artifacts =========="

                    rm -rf deploy-artifacts
                    mkdir -p deploy-artifacts


                    echo "Saving tested Docker images..."

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

                    CREATED_AT="$(
                        date -u '+%Y-%m-%dT%H:%M:%SZ'
                    )"

                    ARCHIVE_SHA256="$(
                        awk '{print $1}' \
                            deploy-artifacts/mini-soar-images.tar.gz.sha256
                    )"


                    printf '%s\n' \
                        "BUILD_NUMBER=${BUILD_NUMBER}" \
                        "COMMIT_SHA=${COMMIT_SHA}" \
                        "CREATED_AT=${CREATED_AT}" \
                        "ARCHIVE_SHA256=${ARCHIVE_SHA256}" \
                        "DEMO_WEB_IMAGE=${DEMO_WEB_IMAGE}" \
                        "MINI_SOAR_API_IMAGE=${MINI_SOAR_API_IMAGE}" \
                        "DASHBOARD_IMAGE=${DASHBOARD_IMAGE}" \
                        > deploy-artifacts/deployment.env


                    echo ""
                    echo "Artifacts:"

                    ls -lah deploy-artifacts/


                    echo ""
                    echo "Deployment metadata:"

                    cat deploy-artifacts/deployment.env


                    echo ""
                    echo "Artifact checksum:"

                    cat \
                        deploy-artifacts/mini-soar-images.tar.gz.sha256

                    echo ""
                    echo "Artifact packaging PASS"
                '''


                // ----------------------------------------------------
                // Preserve deployment artifacts
                // ----------------------------------------------------

                stash(
                    name: 'deployment-artifacts',
                    includes: 'deploy-artifacts/**,deploy-artifacts/.deploy.env',
                    useDefaultExcludes: false
                )


                archiveArtifacts(
                    artifacts: 'deploy-artifacts/deployment.env',
                    fingerprint: true
                )


                sh '''
                    echo ""
                    echo "======================================"
                    echo " BUILD & TEST PASS"
                    echo "======================================"
                '''
            }
        }


        // ============================================================
        // 3. DEPLOY
        // ============================================================

        stage('Deploy') {
            steps {

                // Supports Restart from Deploy.
                unstash 'deployment-artifacts'


                sshagent(credentials: ['mini-soar-deploy-ssh']) {

                    // ------------------------------------------------
                    // Connectivity + backup + transfer
                    // ------------------------------------------------

                    sh '''
                        set -e

                        echo "======================================"
                        echo " Mini-SOAR - DEPLOY"
                        echo "======================================"

                        TARGET="${DEPLOY_USER}@${DEPLOY_HOST}"


                        ssh_remote() {
                            ssh \
                                -o BatchMode=yes \
                                -o StrictHostKeyChecking=yes \
                                -o ConnectTimeout=10 \
                                -o ConnectionAttempts=2 \
                                "$@"
                        }


                        scp_remote() {
                            scp \
                                -o BatchMode=yes \
                                -o StrictHostKeyChecking=yes \
                                -o ConnectTimeout=10 \
                                -o ConnectionAttempts=2 \
                                "$@"
                        }


                        echo ""
                        echo "========== SSH =========="

                        ssh_remote \
                            "${TARGET}" \
                            "mkdir -p ${DEPLOY_DIR}"

                        echo "SSH connectivity PASS"


                        echo ""
                        echo "========== Backup Current Release =========="

                        ssh_remote \
                            "${TARGET}" \
                            "
                                set -e

                                cd ${DEPLOY_DIR}

                                SAME_BUILD=false

                                if [ -f deployment.env ] &&
                                   grep -Fxq \
                                       'BUILD_NUMBER=${BUILD_NUMBER}' \
                                       deployment.env
                                then
                                    SAME_BUILD=true
                                fi

                                if [ \\"\\${SAME_BUILD}\\" = false ]
                                then
                                    if [ -f .deploy.env ]
                                    then
                                        cp \
                                            .deploy.env \
                                            .deploy.env.previous
                                    fi

                                    if [ -f docker-compose.yml ]
                                    then
                                        cp \
                                            docker-compose.yml \
                                            docker-compose.previous.yml
                                    fi

                                    if [ -f deployment.env ]
                                    then
                                        cp \
                                            deployment.env \
                                            deployment.previous.env
                                    fi

                                    echo 'Previous release backed up.'
                                else
                                    echo \
                                      'Same build already staged; preserving previous backup.'
                                fi
                            "


                        echo ""
                        echo "========== Transfer =========="

                        scp_remote \
                            deploy-artifacts/mini-soar-images.tar.gz \
                            deploy-artifacts/mini-soar-images.tar.gz.sha256 \
                            deploy-artifacts/docker-compose.yml \
                            deploy-artifacts/.deploy.env \
                            deploy-artifacts/deployment.env \
                            "${TARGET}:${DEPLOY_DIR}/"

                        echo "Artifact transfer PASS"
                    '''


                    // Actual runtime is about to be modified.
                    script {
                        env.DEPLOY_ATTEMPTED = 'true'
                    }


                    // ------------------------------------------------
                    // Deploy
                    // ------------------------------------------------

                    sh '''
                        set -e

                        TARGET="${DEPLOY_USER}@${DEPLOY_HOST}"

                        ssh_remote() {
                            ssh \
                                -o BatchMode=yes \
                                -o StrictHostKeyChecking=yes \
                                -o ConnectTimeout=10 \
                                -o ConnectionAttempts=2 \
                                "$@"
                        }


                        echo ""
                        echo "========== Deploy Tested Artifact =========="


                        ssh_remote \
                            "${TARGET}" \
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

                                echo 'Deployment files PASS'


                                echo ''
                                echo 'Verifying SHA256...'

                                sha256sum \
                                    -c mini-soar-images.tar.gz.sha256

                                echo 'Artifact checksum PASS'


                                echo ''
                                echo 'Loading tested Docker images...'

                                gzip -dc \
                                    mini-soar-images.tar.gz \
                                    | docker load


                                echo ''
                                echo 'Validating production Compose...'

                                docker compose \
                                    --env-file .deploy.env \
                                    -f docker-compose.yml \
                                    config \
                                    >/dev/null

                                echo 'Production Compose PASS'


                                echo ''
                                echo 'Starting application...'

                                docker compose \
                                    --env-file .deploy.env \
                                    -f docker-compose.yml \
                                    up -d \
                                    --no-build


                                echo ''
                                echo 'Deployment state:'

                                docker compose \
                                    --env-file .deploy.env \
                                    -f docker-compose.yml \
                                    ps
                            "

                        echo ""
                        echo "Compose deployment PASS"
                    '''


                    // ------------------------------------------------
                    // Post-deployment verification
                    // ------------------------------------------------

                    sh '''
                        set -e

                        TARGET="${DEPLOY_USER}@${DEPLOY_HOST}"

                        ssh_remote() {
                            ssh \
                                -o BatchMode=yes \
                                -o StrictHostKeyChecking=yes \
                                -o ConnectTimeout=10 \
                                -o ConnectionAttempts=2 \
                                "$@"
                        }


                        wait_http() {
                            NAME="$1"
                            URL="$2"
                            CONTAINER="$3"
                            ATTEMPTS="${4:-30}"

                            for attempt in $(seq 1 "$ATTEMPTS")
                            do
                                if curl \
                                    --fail \
                                    --silent \
                                    --show-error \
                                    "$URL" \
                                    >/dev/null
                                then
                                    echo "[PASS] ${NAME}"
                                    return 0
                                fi

                                echo \
                                    "[${attempt}/${ATTEMPTS}] Waiting for ${NAME}..."

                                sleep 2
                            done


                            echo "[FAIL] ${NAME}"


                            if [ -n "$CONTAINER" ]
                            then
                                echo ""
                                echo "========== ${CONTAINER} logs =========="

                                ssh_remote \
                                    "${TARGET}" \
                                    "docker logs --tail 100 ${CONTAINER}" \
                                    || true
                            fi

                            return 1
                        }


                        echo ""
                        echo "========== Post-Deployment Verification =========="


                        wait_http \
                            "demo-web" \
                            "http://${DEPLOY_HOST}:8000/health" \
                            "demo-web"


                        wait_http \
                            "Mini-SOAR API" \
                            "http://${DEPLOY_HOST}:9000/health" \
                            "mini-soar-api"


                        wait_http \
                            "Dashboard" \
                            "http://${DEPLOY_HOST}:8080/healthz" \
                            "mini-soar-dashboard"


                        echo ""
                        echo "Testing dashboard reverse proxy..."

                        curl \
                            --fail \
                            --silent \
                            --show-error \
                            "http://${DEPLOY_HOST}:8080/api/v1/remediations/summary" \
                            >/dev/null

                        echo "Dashboard reverse proxy PASS"


                        echo ""
                        echo "Testing API database access..."

                        curl \
                            --fail \
                            --silent \
                            --show-error \
                            "http://${DEPLOY_HOST}:9000/api/v1/remediations/summary" \
                            >/dev/null

                        echo "API database access PASS"


                        echo ""
                        echo "Verifying deployed image versions..."


                        REMOTE_IMAGES="$(
                            ssh_remote \
                                "${TARGET}" \
                                "docker inspect \
                                    --format '{{.Name}}={{.Config.Image}}' \
                                    demo-web \
                                    mini-soar-api \
                                    mini-soar-dashboard"
                        )"


                        echo "${REMOTE_IMAGES}"


                        echo "${REMOTE_IMAGES}" \
                            | grep -Fxq \
                            "/demo-web=${DEMO_WEB_IMAGE}"


                        echo "${REMOTE_IMAGES}" \
                            | grep -Fxq \
                            "/mini-soar-api=${MINI_SOAR_API_IMAGE}"


                        echo "${REMOTE_IMAGES}" \
                            | grep -Fxq \
                            "/mini-soar-dashboard=${DASHBOARD_IMAGE}"


                        echo "Image version verification PASS"


                        echo ""
                        echo "Verifying deployment metadata..."


                        ssh_remote \
                            "${TARGET}" \
                            "grep -Fx \
                                'BUILD_NUMBER=${BUILD_NUMBER}' \
                                ${DEPLOY_DIR}/deployment.env"


                        echo "Deployment metadata PASS"


                        echo ""
                        echo "Remote application state:"


                        ssh_remote \
                            "${TARGET}" \
                            "docker ps \
                                --filter name=demo-web \
                                --filter name=mini-soar-api \
                                --filter name=mini-soar-dashboard \
                                --format \
                                'table {{.Names}}\\t{{.Image}}\\t{{.Status}}'"


                        echo ""
                        echo "Post-deployment verification PASS"
                    '''
                }


                // All runtime checks passed.
                script {
                    env.DEPLOY_VERIFIED = 'true'
                }


                // ----------------------------------------------------
                // Finalize
                // ----------------------------------------------------

                sshagent(credentials: ['mini-soar-deploy-ssh']) {
                    sh '''
                        set +e

                        echo ""
                        echo "========== Finalize =========="


                        ssh \
                            -o BatchMode=yes \
                            -o StrictHostKeyChecking=yes \
                            -o ConnectTimeout=10 \
                            -o ConnectionAttempts=2 \
                            "${DEPLOY_USER}@${DEPLOY_HOST}" \
                            "
                                cd ${DEPLOY_DIR} || exit 0

                                rm -f \
                                    mini-soar-images.tar.gz \
                                    mini-soar-images.tar.gz.sha256

                                docker image prune -f || true
                            "


                        echo "Deployment cleanup completed."

                        echo ""
                        echo "======================================"
                        echo " DEPLOY PASS"
                        echo "======================================"
                    '''
                }
            }
        }
    }


    // ================================================================
    // POST
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

                    echo \
                        'Deployment failed after runtime modification started. Attempting rollback...'


                    sshagent(
                        credentials: ['mini-soar-deploy-ssh']
                    ) {

                        sh '''
                            set +e

                            echo ""
                            echo "======================================"
                            echo " AUTOMATIC ROLLBACK"
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
                                        echo \
                                            'Rollback unavailable: no previous release.'

                                        exit 2
                                    fi


                                    echo ''
                                    echo 'Previous release:'

                                    cat .deploy.env.previous


                                    echo ''
                                    echo 'Restoring previous release...'


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
                                    echo 'Waiting for rollback services...'

                                    sleep 10


                                    echo ''
                                    echo 'Rollback state:'


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
                                echo \
                                    "Automatic rollback completed successfully."
                            else
                                echo ""
                                echo \
                                    "WARNING: automatic rollback failed."

                                echo \
                                    "Rollback exit code: ${ROLLBACK_RC}"

                                echo \
                                    "Manual recovery may be required."
                            fi


                            # Preserve original Jenkins failure.
                            exit 0
                        '''
                    }

                } else {

                    echo "Rollback not required."
                    echo \
                        "DEPLOY_ATTEMPTED=${env.DEPLOY_ATTEMPTED}"
                    echo \
                        "DEPLOY_VERIFIED=${env.DEPLOY_VERIFIED}"
                }
            }


            echo \
                'Mini-SOAR CI/CD pipeline FAILED. Check the failed step above.'
        }


        // ------------------------------------------------------------
        // CI cleanup
        // ------------------------------------------------------------

        always {

            sh '''
                set +e

                echo ""
                echo "======================================"
                echo " Jenkins CI Cleanup"
                echo "======================================"


                docker compose \
                    -f docker-compose.ci.yml \
                    down \
                    --volumes \
                    --remove-orphans \
                    || true


                docker image rm \
                    "${DEMO_WEB_IMAGE}" \
                    "${MINI_SOAR_API_IMAGE}" \
                    "${DASHBOARD_IMAGE}" \
                    2>/dev/null \
                    || true


                docker image prune -f || true


                docker builder prune \
                    -f \
                    --filter 'until=168h' \
                    || true


                rm -rf \
                    .jenkins-venv \
                    deploy-artifacts \
                    || true


                echo "Jenkins cleanup completed."
            '''


            cleanWs(
                deleteDirs: true,
                disableDeferredWipeout: true
            )
        }


        // ------------------------------------------------------------
        // Success summary
        // ------------------------------------------------------------

        success {

            echo """
======================================
 Mini-SOAR CI/CD SUCCESS
======================================

Pipeline:
  Check                     PASS
  Build & Test              PASS
  Deploy                    PASS

Validation:
  Backend                   PASS
  Frontend                  PASS
  Docker Compose            PASS

Integration:
  API                       PASS
  MariaDB                   PASS
  Dashboard proxy           PASS
  Docker control plane      PASS
  Self-healing              PASS
  Audit persistence         PASS

Deployment:
  Main branch gate          PASS
  SHA256 validation         PASS
  Artifact transfer         PASS
  Docker load               PASS
  Compose deployment        PASS
  Post-deploy verification  PASS
  Image version verify      PASS

Build:
  ${BUILD_NUMBER}

Images:
  ${DEMO_WEB_IMAGE}
  ${MINI_SOAR_API_IMAGE}
  ${DASHBOARD_IMAGE}

======================================
"""
        }
    }
}