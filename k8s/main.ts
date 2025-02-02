import { Construct } from 'constructs';
import { App } from 'cdk8s';
import { Application, PennLabsChart } from '@pennlabs/kittyhawk';


export class MyChart extends PennLabsChart {
  constructor(scope: Construct) {
    super(scope);

    const backendImage = 'pennlabs/penn-mobile-notification-backend';
    const secret = "penn-mobile";

    const ingressProps = {
      annotations: {
        ['ingress.kubernetes.io/content-security-policy']: "frame-ancestors 'none';",
        ["ingress.kubernetes.io/protocol"]: "https",
        ["traefik.ingress.kubernetes.io/router.middlewares"]: "default-redirect-http@kubernetescrd"
      }
    }

    new Application(this, 'backend', {
      deployment: {
        image: backendImage,
        secret,
        replicas: 1,
      },
      ingress: {
        rules: [{
          host: "pennmobile.org",
          paths: ["/notifications"],
        }],
        ...ingressProps,
      }
    });
  }
}

const app = new App();
new MyChart(app);
app.synth();