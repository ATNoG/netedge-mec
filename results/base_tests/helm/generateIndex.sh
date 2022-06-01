mkdir -p helm-repository
for i in $(ls charts/hello-world/Chart.yaml);do
	echo "Building $(dirname $i)"
	helm package -u "$(dirname $i)" -d helm-repository

done
