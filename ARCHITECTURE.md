\# ARCHITECTURE.md — Technical Guidelines



\## File Tree Blueprint

The project directory must strictly follow this structural design:

```text

cluster-heist/

&#x20; README.md

&#x20; SKILLS.md

&#x20; ARCHITECTURE.md

&#x20; cli/

&#x20;   src/

&#x20;     main.py

&#x20;   .cluster-heist-state.json

&#x20;   requirements.txt

&#x20; charts/

&#x20;   cluster-heist/

&#x20;     Chart.yaml

&#x20;     values.yaml

&#x20;     templates/

&#x20;       deployment-message.yaml

&#x20;       service-message.yaml

&#x20;       deployment-greeting.yaml

&#x20;       service-greeting.yaml

&#x20;       ingress.yaml

&#x20;       configmap.yaml

&#x20;       secret.yaml

&#x20;       redis.yaml

&#x20;       sidecar-logger.yaml

&#x20; k8s/

&#x20;   broken/

&#x20;   fixed/

&#x20; scripts/

&#x20;   setup.sh

&#x20;   reset.sh

