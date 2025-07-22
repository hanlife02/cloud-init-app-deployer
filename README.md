添加公钥

```
openstack keypair create --public-key ~/.ssh/id_rsa.pub mykey_name
```

启动实例
```
openstack server create --image "Ubuntu 22.04"  --flavor e1 --network pku-new  --user-data config.yaml --key-name mykey_name test-id
```