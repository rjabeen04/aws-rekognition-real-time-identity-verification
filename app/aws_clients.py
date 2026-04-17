import boto3
import streamlit as st
from app.config import DYNAMO_TABLE

@st.cache_resource
def init_clients():
    try:
        rekognition = boto3.client('rekognition', region_name='us-east-1')
        s3 = boto3.client('s3', region_name='us-east-1')
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table(DYNAMO_TABLE)
        table_registry = dynamodb.Table('SecureGuard_Registry')
        return rekognition, s3, table, table_registry
    except Exception as e:
        st.error(f"AWS client init failed: {e}")
        st.stop()
