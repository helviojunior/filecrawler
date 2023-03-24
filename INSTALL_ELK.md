# ELK - Indexando Arquivos

**Note:** By now only in Brazilian language (PT-BR)

O Objetivo deste tutorial é criar uma estrutura utilizando o ELK para indexar conteúdos de arquivos facilitando a busca durante um teste.

No cenário utilizado obtivemos acesso a mais de 120GB de dados baixados de um GIT do cliente, sendo assim qualquer busca utilizando GREP seria praticamente impossível e demandaria muito tempo. Neste procedimento indexamos os arquivos uma unica vez dentro do ELK (processo este que demora de 2 a 3 horas dependendo do disco e quantidade de arquivos) e posteriormente as buscas são instanâneas.

Sem contar que temos a possibilidade de diversas consultas avançadas com a linguagem de consultas do ELK.

## Dependencias gerais

### Instalando outras dependencias

```
apt install python3 python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools python3-venv unzip
```

## ELK

### Instalando o ELK

```
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-8.x.list
sudo apt update
sudo apt install elasticsearch kibana
```

### Configurando o ELK

Edite o arquivo sudo nano /etc/elasticsearch/elasticsearch.yml alterando o bind para somente localhost

```
network.host: 127.0.0.1
http.host: 127.0.0.1
http.port: 9200
```

Caso queira que o elasticsearch faça bind em todas as interfaces
Edite o arquivo /etc/elasticsearch/elasticsearch.yml

**Nota:** Esta configuração será necessária caso o crawler execute em uma maquina diferente do servidor ELK

```
network.host: 127.0.0.1
http.host: 0.0.0.0
http.port: 9200
```

#### Edite o nome do cluster
Edite o arquivo /etc/elasticsearch/elasticsearch.yml

```
cluster.name: my-application
node.name: node-1
```

#### Ajuste as configurações de segurança
Edite o arquivo /etc/elasticsearch/elasticsearch.yml

```
# Enable security features
xpack.security.enabled: false

xpack.security.enrollment.enabled: false

# Enable encryption for HTTP API client connections, such as Kibana, Logstash, and Agents
xpack.security.http.ssl:
  enabled: false
  keystore.path: certs/http.p12

# Enable encryption and mutual authentication between cluster nodes
xpack.security.transport.ssl:
  enabled: false
```

#### Ajuste os limites JVM

Ajuste com em torno de 80% da memória da máquina. Edite o arquivo /etc/elasticsearch/jvm.options

```
-Xms1g
-Xmx1g
```


### Habilite o serviço do ELK
```
systemctl enable elasticsearch
systemctl start elasticsearch
systemctl enable kibana
systemctl start kibana
```

### Ajustando local de armazenamento

**Nota:** Este item é opcional, mas recomendado em caso de grandes armazenamentos de dados

Monte o disco externo em um diretório qualquer, em nosso lab montamos em /u01/es_data/

Sincronize o conteúdo atual para o novo diretório
```
rsync -av /var/lib/elasticsearch* /u01/es_data/
```

Edite /etc/elasticsearch/elasticsearch.yml

Altere de **path.data: /var/lib/elasticsearch** para 

```
path.data: /u01/es_data/elasticsearch
```

Reinicie o serviço do elasticsearch
```
systemctl restart elasticsearch
```

### Testando
```
curl -k -X GET "http://localhost:9200"
```

Terá como resposta algo similar ao abaixo

```
{
  "name" : "elklab",
  "cluster_name" : "elasticsearch",
  "cluster_uuid" : "_Pctj2CzSqOTgHNFOXZZjg",
  "version" : {
    "number" : "7.16.0",
    "build_flavor" : "default",
    "build_type" : "deb",
    "build_hash" : "6fc81662312141fe7691d7c1c91b8658ac17aa0d",
    "build_date" : "2021-12-02T15:46:35.697268109Z",
    "build_snapshot" : false,
    "lucene_version" : "8.10.1",
    "minimum_wire_compatibility_version" : "6.8.0",
    "minimum_index_compatibility_version" : "6.0.0-beta1"
  },
  "tagline" : "You Know, for Search"
}
```

### Publicando e protegendo o Kibana


#### Instalando o NGINX


```
echo deb http://nginx.org/packages/mainline/ubuntu/ `lsb_release --codename --short` nginx > /etc/apt/sources.list.d/nginx.list
curl -s http://nginx.org/keys/nginx_signing.key | apt-key add -
sudo apt update
sudo apt install nginx
```

#### Configurando o NGINX

Edite o arquivo /etc/nginx/nginx.conf para que o mesmo fique exatamente conforme abaixo:

```
user  nginx;
worker_processes  1;
 
error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;
 
 
events {
    worker_connections  1024;
}
 
 
http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
 
    limit_conn_zone $binary_remote_addr zone=addr:10m;
    server_names_hash_bucket_size  256;
 
    client_max_body_size 10m;
 
    log_format log_standard '$remote_addr, $http_x_forwarded_for - $remote_user [$time_local] "$request_method $scheme://$host$request_uri $server_protocol" $status $body_bytes_sent "$http_referer" "$http_user_agent" to: $upstream_addr';
 
    access_log /var/log/nginx/access.log log_standard;
    error_log /var/log/nginx/error.log;
 
    sendfile        on;
    #tcp_nopush     on;
 
    keepalive_timeout  65;
 
    #gzip  on;
 
    include /etc/nginx/conf.d/*.conf;
}
```

Crie/edite o arquivo /etc/nginx/conf.d/default.conf conforme o conteúdo abaixo


```
server {
    listen 80;

    server_name _;

    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/htpasswd.users;

    location / {
        proxy_pass http://127.0.0.1:5601;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

#### Criação user admin
```
echo "admin:`openssl passwd -apr1`" | sudo tee -a /etc/nginx/htpasswd.users
```

#### Habilitando o serviço do NGINX
```
sudo systemctl enable nginx
sudo systemctl start nginx
```
