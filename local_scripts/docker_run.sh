source ../container-name.sh

IMAGE_NAME=$1

if [ $# -lt 1 ];
then
    echo "+ $0: Too few arguments!"
    echo "+ use something like:"
    echo "+ $0 <docker image>" 
    echo "+ $0 reslocal/${CONTAINER_NAME}:latest"
    exit
fi

echo "do the following:"
echo "docker run --rm -d --name rauc-test -p 9998:9998 ${IMAGE_NAME}"
echo "docker exec rauc-test rauc --version"
echo "docker exec rauc-test openssl engine -t pkcs11"
echo "docker exec rauc-test ykman --version"
echo "docker exec rauc-test ls -l /usr/lib/x86_64-linux-gnu/opensc-pkcs11.so"
echo "curl -i http://localhost:9998/health"
echo "docker stop rauc-test"
