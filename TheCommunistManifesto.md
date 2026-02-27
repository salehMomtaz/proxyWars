```
apiVersion: apps/v1
kind: Deployment
metadata:
    annotations:
        deployment.kubernetes.io/revision: "2"
    generation: 3
    labels:
        app: x
    name: x
spec:
    progressDeadlineSeconds: 600
    replicas: 0
    revisionHistoryLimit: 3
    selector:
        matchLabels:
            app: x
    strategy:
        type: Recreate
    template:
        metadata:
            creationTimestamp: null
            labels:
                app: x
                name: x
        spec:
            affinity:
                nodeAffinity:
                    requiredDuringSchedulingIgnoredDuringExecution:
                        nodeSelectorTerms:
                            - matchExpressions:
                                  - key: node-role.kubernetes.io/cloud-container-g2
                                    operator: In
                                    values:
                                        - "true"
            containers:
                - image: ghcr.io/mhsanaei/3x-ui:latest
                  imagePullPolicy: Always
                  name: x
                  ports:
                      - containerPort: 2053
                        name: http
                        protocol: TCP
                  resources:
                      limits:
                          cpu: 100m
                          ephemeral-storage: 300M
                          memory: 200M
                      requests:
                          cpu: 100m
                          ephemeral-storage: 300M
                          memory: 200M
                  terminationMessagePath: /dev/termination-log
                  terminationMessagePolicy: File
                  volumeMounts:
                      - mountPath: /etc/x-ui
                        name: x-disk-x
            dnsPolicy: ClusterFirst
            restartPolicy: Always
            schedulerName: default-scheduler
            securityContext: {}
            terminationGracePeriodSeconds: 30
            tolerations:
                - effect: NoSchedule
                  key: role
                  operator: Equal
                  value: cloud-container-g2
            volumes:
                - name: x-disk-x
                  persistentVolumeClaim:
                      claimName: x-disk-x
---
kind: Service
metadata:
    labels:
        app: x
    name: x
spec:
    clusterIP: x
    clusterIPs:
        - x
    internalTrafficPolicy: Cluster
    ipFamilies:
        - IPv4
    ipFamilyPolicy: SingleStack
    ports:
        - name: http
          port: 80
          protocol: TCP
          targetPort: http
    selector:
        app: x
    sessionAffinity: None
    type: ClusterIP
---
kind: Ingress
metadata:
    generation: 1
    name: x
spec:
    ingressClassName: nginx
    rules:
        - host: x.apps.ir-central1.arvancaas.ir
          http:
              paths:
                  - backend:
                        service:
                            name: x
                            port:
                                number: 80
                    path: /
                    pathType: Prefix
---
kind: PersistentVolumeClaim
metadata:
    annotations:
        pv.kubernetes.io/bind-completed: yes
        pv.kubernetes.io/bound-by-controller: yes
        volume.beta.kubernetes.io/storage-provisioner: cinder.csi.openstack.org
        volume.kubernetes.io/selected-node: caas-prd-worker-ba-123
        volume.kubernetes.io/storage-provisioner: cinder.csi.openstack.org
    finalizers:
        - kubernetes.io/pvc-protection
    name: x-disk-x
spec:
    accessModes:
        - ReadWriteOnce
    resources:
        requests:
            storage: 1G
    storageClassName: csi-cinder-sc-delete-az
    volumeMode: Filesystem
    volumeName: pvc-x
```
