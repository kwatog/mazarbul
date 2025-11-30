pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = credentials('docker-registry')
        DOCKER_REPO = 'mazarbul'
        KUBECONFIG = credentials('kubeconfig')
        HELM_CHART_VERSION = "${env.BUILD_NUMBER}"
    }
    
    parameters {
        choice(
            name: 'DEPLOYMENT_TARGET',
            choices: ['development', 'staging', 'production'],
            description: 'Select deployment target environment'
        )
        booleanParam(
            name: 'DEPLOY_BACKEND',
            defaultValue: true,
            description: 'Deploy backend service'
        )
        booleanParam(
            name: 'DEPLOY_FRONTEND',
            defaultValue: true,
            description: 'Deploy frontend service'
        )
        booleanParam(
            name: 'SKIP_TESTS',
            defaultValue: false,
            description: 'Skip running tests'
        )
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                    env.IMAGE_TAG = "${env.DEPLOYMENT_TARGET}-${env.GIT_COMMIT_SHORT}-${env.BUILD_NUMBER}"
                }
            }
        }
        
        stage('Test Backend') {
            when {
                allOf {
                    params.DEPLOY_BACKEND
                    not { params.SKIP_TESTS }
                }
            }
            steps {
                dir('backend') {
                    sh '''
                        python -m venv venv
                        source venv/bin/activate
                        pip install -r requirements.txt
                        # Add test commands here when tests are available
                        # python -m pytest tests/
                        echo "Backend tests would run here"
                    '''
                }
            }
        }
        
        stage('Test Frontend') {
            when {
                allOf {
                    params.DEPLOY_FRONTEND
                    not { params.SKIP_TESTS }
                }
            }
            steps {
                dir('frontend') {
                    sh '''
                        npm ci
                        # Add test commands here when tests are available
                        # npm run test
                        npm run build
                        echo "Frontend tests would run here"
                    '''
                }
            }
        }
        
        stage('Build Backend Image') {
            when { params.DEPLOY_BACKEND }
            steps {
                dir('backend') {
                    script {
                        def backendImage = docker.build("${DOCKER_REPO}/backend:${IMAGE_TAG}")
                        docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-registry-creds') {
                            backendImage.push()
                            backendImage.push("${DEPLOYMENT_TARGET}-latest")
                        }
                    }
                }
            }
        }
        
        stage('Build Frontend Image') {
            when { params.DEPLOY_FRONTEND }
            steps {
                dir('frontend') {
                    script {
                        def frontendImage = docker.build("${DOCKER_REPO}/frontend:${IMAGE_TAG}")
                        docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-registry-creds') {
                            frontendImage.push()
                            frontendImage.push("${DEPLOYMENT_TARGET}-latest")
                        }
                    }
                }
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    def helmValues = []
                    
                    // Environment-specific values
                    def valuesFile = "helm/mazarbul/values-${DEPLOYMENT_TARGET}.yaml"
                    if (fileExists(valuesFile)) {
                        helmValues.add("-f ${valuesFile}")
                    }
                    
                    // Image tags
                    if (params.DEPLOY_BACKEND) {
                        helmValues.add("--set backend.image.tag=${IMAGE_TAG}")
                    }
                    if (params.DEPLOY_FRONTEND) {
                        helmValues.add("--set frontend.image.tag=${IMAGE_TAG}")
                    }
                    
                    // Component enablement
                    helmValues.add("--set backend.enabled=${params.DEPLOY_BACKEND}")
                    helmValues.add("--set frontend.enabled=${params.DEPLOY_FRONTEND}")
                    
                    // Registry configuration
                    helmValues.add("--set global.imageRegistry=${DOCKER_REGISTRY}")
                    
                    def helmCommand = """
                        helm upgrade --install mazarbul-${DEPLOYMENT_TARGET} ./helm/mazarbul \\
                            --namespace mazarbul-${DEPLOYMENT_TARGET} \\
                            --create-namespace \\
                            ${helmValues.join(' ')} \\
                            --wait \\
                            --timeout 10m
                    """
                    
                    sh helmCommand
                }
            }
        }
        
        stage('Verify Deployment') {
            steps {
                script {
                    sh """
                        kubectl get pods -n mazarbul-${DEPLOYMENT_TARGET}
                        kubectl get services -n mazarbul-${DEPLOYMENT_TARGET}
                        
                        # Wait for deployments to be ready
                        if [ "${params.DEPLOY_BACKEND}" = "true" ]; then
                            kubectl rollout status deployment/mazarbul-${DEPLOYMENT_TARGET}-backend -n mazarbul-${DEPLOYMENT_TARGET}
                        fi
                        
                        if [ "${params.DEPLOY_FRONTEND}" = "true" ]; then
                            kubectl rollout status deployment/mazarbul-${DEPLOYMENT_TARGET}-frontend -n mazarbul-${DEPLOYMENT_TARGET}
                        fi
                    """
                }
            }
        }
        
        stage('Smoke Tests') {
            when {
                not { params.SKIP_TESTS }
            }
            steps {
                script {
                    if (params.DEPLOY_BACKEND) {
                        sh """
                            # Wait for backend to be ready and test health endpoint
                            echo "Testing backend health endpoint..."
                            kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=backend -n mazarbul-${DEPLOYMENT_TARGET} --timeout=300s
                            
                            # Port-forward and test (or use ingress URL if available)
                            kubectl port-forward svc/mazarbul-${DEPLOYMENT_TARGET}-backend 8080:8000 -n mazarbul-${DEPLOYMENT_TARGET} &
                            KUBECTL_PID=\$!
                            sleep 10
                            
                            curl -f http://localhost:8080/health || exit 1
                            kill \$KUBECTL_PID
                        """
                    }
                    
                    if (params.DEPLOY_FRONTEND) {
                        sh """
                            # Test frontend availability
                            echo "Testing frontend availability..."
                            kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=frontend -n mazarbul-${DEPLOYMENT_TARGET} --timeout=300s
                            
                            # Port-forward and test (or use ingress URL if available)
                            kubectl port-forward svc/mazarbul-${DEPLOYMENT_TARGET}-frontend 3080:3000 -n mazarbul-${DEPLOYMENT_TARGET} &
                            KUBECTL_PID=\$!
                            sleep 10
                            
                            curl -f http://localhost:3080/health || exit 1
                            kill \$KUBECTL_PID
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Clean up Docker images to save space
            sh '''
                docker image prune -f
                docker system prune -f --volumes
            '''
        }
        
        success {
            echo "Deployment to ${params.DEPLOYMENT_TARGET} completed successfully!"
            script {
                if (params.DEPLOYMENT_TARGET == 'production') {
                    // Send notification for production deployments
                    slackSend(
                        channel: '#deployments',
                        color: 'good',
                        message: "✅ Mazarbul production deployment successful! Version: ${IMAGE_TAG}"
                    )
                }
            }
        }
        
        failure {
            echo "Deployment to ${params.DEPLOYMENT_TARGET} failed!"
            script {
                // Send failure notification
                slackSend(
                    channel: '#deployments',
                    color: 'danger',
                    message: "❌ Mazarbul ${params.DEPLOYMENT_TARGET} deployment failed! Build: ${env.BUILD_URL}"
                )
            }
        }
        
        cleanup {
            // Clean workspace
            cleanWs()
        }
    }
}