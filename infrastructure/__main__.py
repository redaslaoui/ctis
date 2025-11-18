"""AWS infrastructure for Clinical Trial Intelligence Platform"""
import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx

# Configuration
config = pulumi.Config()
environment = pulumi.get_stack()

# VPC
vpc = awsx.ec2.Vpc(
    "ctis-vpc",
    cidr_block="10.0.0.0/16",
    number_of_availability_zones=2,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": f"ctis-vpc-{environment}",
        "Environment": environment,
    }
)

# Security Group for ECS
ecs_security_group = aws.ec2.SecurityGroup(
    "ctis-ecs-sg",
    vpc_id=vpc.vpc_id,
    description="Security group for CTIS ECS tasks",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=8000,
            to_port=8000,
            cidr_blocks=["0.0.0.0/0"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=3000,
            to_port=3000,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    tags={
        "Name": f"ctis-ecs-sg-{environment}",
        "Environment": environment,
    }
)

# RDS PostgreSQL Database
db_security_group = aws.ec2.SecurityGroup(
    "ctis-db-sg",
    vpc_id=vpc.vpc_id,
    description="Security group for CTIS RDS database",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=5432,
            to_port=5432,
            security_groups=[ecs_security_group.id],
        ),
    ],
    tags={
        "Name": f"ctis-db-sg-{environment}",
        "Environment": environment,
    }
)

db_subnet_group = aws.rds.SubnetGroup(
    "ctis-db-subnet-group",
    subnet_ids=vpc.private_subnet_ids,
    tags={
        "Name": f"ctis-db-subnet-group-{environment}",
        "Environment": environment,
    }
)

database = aws.rds.Instance(
    "ctis-db",
    allocated_storage=20,
    engine="postgres",
    engine_version="15.4",
    instance_class="db.t3.micro",
    db_name="ctis",
    username="postgres",
    password=config.require_secret("db_password"),
    db_subnet_group_name=db_subnet_group.name,
    vpc_security_group_ids=[db_security_group.id],
    skip_final_snapshot=True,
    tags={
        "Name": f"ctis-db-{environment}",
        "Environment": environment,
    }
)

# ElastiCache Redis
redis_subnet_group = aws.elasticache.SubnetGroup(
    "ctis-redis-subnet-group",
    subnet_ids=vpc.private_subnet_ids,
    tags={
        "Name": f"ctis-redis-subnet-group-{environment}",
        "Environment": environment,
    }
)

redis_security_group = aws.ec2.SecurityGroup(
    "ctis-redis-sg",
    vpc_id=vpc.vpc_id,
    description="Security group for CTIS Redis cache",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=6379,
            to_port=6379,
            security_groups=[ecs_security_group.id],
        ),
    ],
    tags={
        "Name": f"ctis-redis-sg-{environment}",
        "Environment": environment,
    }
)

redis_cluster = aws.elasticache.Cluster(
    "ctis-redis",
    engine="redis",
    node_type="cache.t3.micro",
    num_cache_nodes=1,
    parameter_group_name="default.redis7",
    port=6379,
    subnet_group_name=redis_subnet_group.name,
    security_group_ids=[redis_security_group.id],
    tags={
        "Name": f"ctis-redis-{environment}",
        "Environment": environment,
    }
)

# S3 Bucket for data storage
data_bucket = aws.s3.Bucket(
    "ctis-data-bucket",
    bucket=f"ctis-data-{environment}",
    tags={
        "Name": f"ctis-data-{environment}",
        "Environment": environment,
    }
)

# ECS Cluster
cluster = aws.ecs.Cluster(
    "ctis-cluster",
    name=f"ctis-cluster-{environment}",
    tags={
        "Name": f"ctis-cluster-{environment}",
        "Environment": environment,
    }
)

# Export outputs
pulumi.export("vpc_id", vpc.vpc_id)
pulumi.export("cluster_name", cluster.name)
pulumi.export("database_endpoint", database.endpoint)
pulumi.export("redis_endpoint", redis_cluster.cache_nodes[0].address)
pulumi.export("data_bucket_name", data_bucket.bucket)
