provider "aws" {
  region = "ap-south-1"
}

resource "aws_security_group" "agri_sg" {
  name = "agri_sg"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

   # Add this to your aws_security_group.agri_sg
ingress {
  from_port   = 8000
  to_port     = 8000
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]
}

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "agri_server" {
  ami           = "ami-0f5ee92e2d63afc18"
  instance_type = "t2.micro"

  key_name = "kaushal"

  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.agri_sg.id]

 user_data = <<-EOF
#!/bin/bash

# log everything
exec > /var/log/user-data.log 2>&1

echo "STARTING SETUP"

# update system
apt update -y

# install docker
apt install -y docker.io

# start docker
systemctl start docker
systemctl enable docker

# wait a bit
sleep 10

# pull image
docker pull kaushal2934/agri-ai

# remove old container
docker rm -f agri-ai || true

# run container
docker run -d --name agri-ai -p 80:8000 \
-e GROQ_API_KEY=YOUR_KEY \
-e OPENWEATHER_API_KEY=YOUR_KEY \
kaushal2934/agri-ai

echo "SETUP COMPLETE"
EOF

  tags = {
    Name = "AgriAI"
  }
}

output "public_ip" {
  value = aws_instance.agri_server.public_ip
}

output "public_url" {
  value = "http://${aws_instance.agri_server.public_ip}/docs"
}