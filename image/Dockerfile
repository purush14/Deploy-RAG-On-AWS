FROM public.ecr.aws/lambda/python:3.13

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install build dependencies for chroma-hnswlib
RUN dnf install -y gcc gcc-c++ make && dnf clean all

# Install the specified packages
RUN pip install -r requirements.txt --upgrade

# For local testing.
EXPOSE 8000

# Set IS_USING_IMAGE_RUNTIME Environment Variable
ENV IS_USING_IMAGE_RUNTIME=True
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/rag_app:${PYTHONPATH}"

# Copy all files in ./src
COPY src/* ${LAMBDA_TASK_ROOT}
COPY src/rag_app ${LAMBDA_TASK_ROOT}/rag_app
COPY src/data/chroma ${LAMBDA_TASK_ROOT}/data/chroma

# Lambda handler — points to the Mangum handler in app_api_handler.py
CMD ["app_api_handler.handler"]
