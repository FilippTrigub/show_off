# Rephrase Endpoint Implementation

## Overview

This document describes the implementation of the `/rephrase` endpoint in the backend that calls the executor, accesses BlackBox content and resources, regenerates content while preserving its ID, and updates MongoDB with the regenerated content under the same ID.

## Endpoints Implemented

### 1. `/rephrase` (POST)
- **Purpose**: Dedicated endpoint for content regeneration using BlackBox AI
- **Method**: POST
- **Request Body**: `RephraseContentRequest`
  ```json
  {
    "content_id": "string",
    "instructions": "string"
  }
  ```
- **Response**: `ContentResponse`
  ```json
  {
    "id": "string",
    "content": "string", 
    "status": "string",
    "message": "string"
  }
  ```

### 2. `/content/{content_id}/rephrase` (POST) - Enhanced
- **Purpose**: Enhanced version of existing rephrase endpoint with BlackBox priority
- **Method**: POST
- **Path Parameter**: `content_id` (string)
- **Request Body**: `RephraseRequest`
  ```json
  {
    "instructions": "string"
  }
  ```

## Implementation Details

### Architecture Flow

1. **Content Retrieval**
   - Fetch original content from MongoDB using `content_controller.get_by_id()`
   - Preserve all original metadata for context

2. **BlackBox AI Integration**
   - Primary: Use BlackBox MCP server via `execute_mcp_client()`
   - Fallback: Use other AI services (OpenAI, Claude) via `execute_with_fallback()`
   - Enhanced prompts leverage BlackBox capabilities and resources

3. **Content Regeneration**
   - Construct enhanced prompts with context information
   - Include repository, platform, branch, and summary metadata
   - Request analysis and improvement while preserving core meaning

4. **MongoDB Update**
   - Update content using `content_controller.update_by_id()`
   - **Preserve original content ID** (key requirement)
   - Store backup of original content
   - Track regeneration metadata

### Key Features

#### ID Preservation
- Content ID remains unchanged after regeneration
- Original document updated in-place in MongoDB
- Maintains referential integrity across the system

#### BlackBox AI Priority
- Primary execution through BlackBox MCP server
- Access to BlackBox tools and resources
- Enhanced content analysis and generation capabilities

#### Metadata Tracking
- Backup of original content
- Regeneration instructions and timestamp
- Server used for regeneration
- Regeneration status tracking

#### Error Handling
- Graceful fallback to alternative AI services
- Comprehensive error messages
- Proper HTTP status codes

### Data Models

#### RephraseContentRequest
```python
class RephraseContentRequest(BaseModel):
    content_id: str
    instructions: str = "Make it more engaging and professional"
```

#### ContentResponse
```python
class ContentResponse(BaseModel):
    id: str
    content: str
    status: str
    message: str
```

### MongoDB Updates

The implementation updates the following fields in MongoDB:

```python
update_data = {
    "content": regenerated_content,
    "status": "regenerated",
    "original_content_backup": original_content,
    "regeneration_instructions": instructions,
    "regenerated_at": timestamp,
    "regenerated_by_server": server_name,
    "regeneration_timestamp": timestamp
}
```

## Usage Examples

### Example 1: Basic Rephrase
```bash
curl -X POST "http://localhost:8001/rephrase" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "507f1f77bcf86cd799439011",
    "instructions": "Make this more engaging with emojis"
  }'
```

### Example 2: Professional Enhancement
```bash
curl -X POST "http://localhost:8001/rephrase" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "507f1f77bcf86cd799439011", 
    "instructions": "Rewrite for LinkedIn audience, professional tone"
  }'
```

### Example 3: Content-Specific Rephrase
```bash
curl -X POST "http://localhost:8001/content/507f1f77bcf86cd799439011/rephrase" \
  -H "Content-Type: application/json" \
  -d '{
    "instructions": "Make more concise and add technical details"
  }'
```

## Error Handling

### Status Codes
- `200`: Success - Content regenerated
- `404`: Content not found with given ID
- `500`: Server error - AI services unavailable or other internal error

### Error Scenarios
1. **Content Not Found**: Invalid or non-existent content_id
2. **BlackBox Unavailable**: Falls back to other AI services
3. **All AI Services Fail**: Returns appropriate error message
4. **MongoDB Connection Issues**: Database operation failures

## Testing

Use the provided test script:
```bash
python backend/test_rephrase_endpoint.py
```

Make sure:
1. Backend server is running on localhost:8001
2. Valid content exists in MongoDB
3. BlackBox API credentials are configured
4. MongoDB connection is established

## Configuration

### Required Environment Variables
- `BLACKBOX_API_KEY`: BlackBox AI API key
- `MONGODB_URI`: MongoDB connection string
- `MONGODB_DB_NAME`: Database name

### Config Files
- `backend/config.yml`: MCP server configurations
- `backend/prompts.yml`: Prompt templates

## Security Considerations

1. **Input Validation**: Validate content_id format and instructions length
2. **Rate Limiting**: Consider implementing rate limits for regeneration
3. **Authentication**: Add user authentication if needed
4. **Content Sanitization**: Sanitize generated content before storage

## Future Enhancements

1. **Batch Processing**: Support multiple content regeneration
2. **Custom Prompts**: Allow custom prompt templates
3. **Version History**: Track multiple regeneration versions
4. **Analytics**: Monitor regeneration performance and success rates
