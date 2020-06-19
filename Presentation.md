---
marp: true
theme: uncover
---

# Welcome !

---

# Problem statement ( chain )

 - IaC is a must nowadays
 - Complexity of the IaC demands fell defined scoop 
 - IaC scooping create isolation bubbles
 - Bridges are created with all kind of different tech

---

# In other words ( picture )
![xkcd](https://imgs.xkcd.com/comics/sandboxing_cycle.png)

---

# Examples

 - Layers of the company
    - Networking stacks
    - Application
    - Core infra
 - Layers of the application
    - DB
    - App
    - CDN

---

# Possible solutions in AWS CFN

 - Manual wire it together
 - CFN import export ( AWS native ) 
 - SSM Parameters ( Hacky but we use it a [lot](https://medium.com/nordcloud-engineering/decoupling-iac-with-ssm-parameter-store-8f38feae3936))
 - Maintain an asset management solution like an API

---

# How others do it ?

Terraform Datasources:
```
Data sources allow data to be fetched or computed for
use elsewhere in Terraform configuration. Use of data sources allows
a Terraform configuration to make use of information defined
outside of Terraform, or defined by another separate
Terraform configuration.
```

---

# Can we steal the idea ?

Sure we can with CFN CR (https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources.html)

---

# Show me the code ! 
