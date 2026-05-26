# Kubernetes Deployment

Deploy LeafMesh on Kubernetes for production-grade scaling and high availability.

## Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: swarm-app
  labels:
    app: swarm-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: swarm-app
  template:
    metadata:
      labels:
        app: swarm-app
    spec:
      containers:
        - name: swarm-app
          image: my-registry/swarm-app:latest
          ports:
            - containerPort: 18820
          env:
            - name: REDIS_HOST
              value: "redis-service"
            - name: OPENAI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: llm-secrets
                  key: openai-api-key
            - name: ANTHROPIC_API_KEY
              valueFrom:
                secretKeyRef:
                  name: llm-secrets
                  key: anthropic-api-key
          livenessProbe:
            httpGet:
              path: /health
              port: 18820
            initialDelaySeconds: 15
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 18820
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
```

## Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: swarm-service
spec:
  selector:
    app: swarm-app
  ports:
    - port: 80
      targetPort: 18820
  type: ClusterIP
```

## Redis StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis-service
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
          command: ["redis-server", "--appendonly", "yes"]
          volumeMounts:
            - name: redis-data
              mountPath: /data
  volumeClaimTemplates:
    - metadata:
        name: redis-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
spec:
  selector:
    app: redis
  ports:
    - port: 6379
  clusterIP: None
```

## Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: llm-secrets
type: Opaque
stringData:
  openai-api-key: "sk-..."
  anthropic-api-key: "sk-ant-..."
  redis-password: "your-redis-password"
```

## Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: swarm-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: swarm-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: swarm-ingress
spec:
  rules:
    - host: swarm.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: swarm-service
                port:
                  number: 80
```

## Key Considerations

| Concern | Approach |
|---------|----------|
| Session affinity | Not required — sessions stored in Redis |
| Scaling | Multiple pods share Redis state |
| Health checks | Liveness/readiness probes on /health |
| Secrets | Kubernetes secrets for API keys |
| Storage | PVC for Redis persistence |
| Networking | ClusterIP service + Ingress |

## Next Steps

- **[Scaling](scaling)** — Scaling strategies
- **[Production Setup](production)** — Production configuration
- **[Monitoring](../observability/monitoring)** — Production monitoring

---

*LeafMesh — Kubernetes deployment guide*
