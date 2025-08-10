import boto3
import streamlit as st
import datetime

st.title("AWS CloudWatch Logs Viewer")

# AWS Credentials Inputs
st.subheader("AWS Credentials")
access_key = st.text_input("AWS Access Key ID", type="password")
secret_key = st.text_input("AWS Secret Access Key", type="password")
region_name = st.text_input("AWS Region", "us-east-1")

if access_key and secret_key:
    # Create boto3 client dynamically
    @st.cache_resource
    def get_logs_client(aws_access_key, aws_secret_key, region):
        return boto3.client(
            'logs',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )

    client = get_logs_client(access_key, secret_key, region_name)

    # List log groups
    @st.cache_data
    def list_log_groups():
        groups = []
        paginator = client.get_paginator('describe_log_groups')
        for page in paginator.paginate():
            for group in page['logGroups']:
                groups.append(group['logGroupName'])
        return groups

    log_groups = list_log_groups()
    selected_group = st.selectbox("Select Log Group", log_groups)

    # List log streams
    @st.cache_data
    def list_log_streams(log_group):
        streams = []
        paginator = client.get_paginator('describe_log_streams')
        for page in paginator.paginate(logGroupName=log_group, orderBy='LastEventTime', descending=True):
            for stream in page['logStreams']:
                streams.append(stream['logStreamName'])
        return streams

    if selected_group:
        log_streams = list_log_streams(selected_group)
        selected_stream = st.selectbox("Select Log Stream", log_streams)

    # Fetch logs
    def get_log_events(log_group, log_stream):
        try:
            response = client.get_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
                startFromHead=True
            )
            events = []
            for event in response['events']:
                timestamp = datetime.datetime.fromtimestamp(event['timestamp'] / 1000)
                message = event['message'].strip()
                events.append(f"[{timestamp}] {message}")
            return events
        except Exception as e:
            return [f"Error fetching logs: {e}"]

    if st.button("Fetch Logs"):
        if selected_group and selected_stream:
            logs = get_log_events(selected_group, selected_stream)
            st.subheader(f"Logs from {selected_stream}")
            st.text_area("Log Output", "\n".join(logs), height=400)

else:
    st.warning("Please enter your AWS credentials to continue.")
