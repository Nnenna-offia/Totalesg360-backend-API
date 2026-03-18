Organization profile API

PATCH /api/v1/organizations/profile/
- Auth: Bearer token
- Headers: `X-ORG-ID: <org_uuid>`
- Content-Type: `multipart/form-data` for file uploads or `application/json` for JSON fields

Example multipart form fields:
- `registered_business_name`: string
- `cac_registration_number`: string
- `company_size`: one of `small|medium|large|enterprise`
- `logo`: file (image/png, image/jpeg)
- `operational_locations`: JSON string (e.g., `["Lagos","Abuja"]`)
- `fiscal_year_start_month`: integer 1-12
- `fiscal_year_end_month`: integer 1-12
- `cac_document`: file (pdf)

Notes:
- When sending files, use multipart/form-data. For clients like curl:

```bash
curl -X PATCH \
  -H "Authorization: Bearer <token>" \
  -H "X-ORG-ID: <org_uuid>" \
  -F "logo=@/path/to/logo.png" \
  -F "registered_business_name=My Co Ltd" \
  https://api.example.com/api/v1/organizations/profile/
```

Business Units

GET /api/v1/organizations/business-units/
POST /api/v1/organizations/business-units/  {"name": "Unit name"}
GET /api/v1/organizations/business-units/<uuid>/
PATCH /api/v1/organizations/business-units/<uuid>/  {"name": "New name"}
DELETE /api/v1/organizations/business-units/<uuid>/
