# Auth implementation details

## OpenID Flow

`/login` triggers an openID flow that ends on `/auth`

Once the JWT is validated, a session token is created and written to 