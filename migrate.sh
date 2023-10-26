export ASPNETCORE_ENVIRONMENT=Development
dotnet ef migrations add InitialCreate
dotnet ef database update