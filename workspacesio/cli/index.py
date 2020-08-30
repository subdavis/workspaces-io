import click

from .config import save_config
from .util import exit_with, handle_request_error


def make(cli: click.Group):
    @cli.group(name="index")
    def index():
        pass

    @index.command(name="create")
    @click.pass_obj
    def register(ctx):
        r = ctx["session"].post("index")
        exit_with(handle_request_error(r))

    cli.add_command(index)

    @index.command(name="test-post")
    @click.pass_obj
    def testpost(ctx):
        r = ctx["session"].post(
            "minio/events",
            json={
                "EventName": "s3:ObjectCreated:Put",
                "Key": "fast/public/main/capture/README.md",
                "Records": [
                    {
                        "eventVersion": "2.0",
                        "eventSource": "minio:s3",
                        "awsRegion": "",
                        "eventTime": "2020-08-30T00:12:42.220Z",
                        "eventName": "s3:ObjectCreated:Put",
                        "userIdentity": {"principalId": "SGEQ69T2808UVLICWN0V"},
                        "requestParameters": {
                            "accessKey": "SGEQ69T2808UVLICWN0V",
                            "region": "",
                            "sourceIPAddress": "172.25.0.1",
                        },
                        "responseElements": {
                            "content-length": "0",
                            "x-amz-request-id": "162FE3588D2BEEB2",
                            "x-minio-deployment-id": "e0133fb2-609d-46f0-9003-bdc829afc9f9",
                            "x-minio-origin-endpoint": "http://172.25.0.4:9000",
                        },
                        "s3": {
                            "s3SchemaVersion": "1.0",
                            "configurationId": "Config",
                            "bucket": {
                                "name": "fast",
                                "ownerIdentity": {
                                    "principalId": "SGEQ69T2808UVLICWN0V"
                                },
                                "arn": "arn:aws:s3:::fast",
                            },
                            "object": {
                                "key": "public%2Fmain%2Fcapture%2FREADME.md",
                                "size": 5892,
                                "eTag": "bea53dca8d059e37af0f7469638d5d52",
                                "contentType": "text/markdown",
                                "userMetadata": {"content-type": "text/markdown"},
                                "sequencer": "162FE3588E1CE6AA",
                            },
                        },
                        "source": {
                            "host": "172.25.0.1",
                            "port": "",
                            "userAgent": "MinIO (linux; amd64) minio-go/v7.0.5 mc/2020-08-20T00:23:01Z",
                        },
                    }
                ],
            },
        )
        exit_with(handle_request_error(r))

