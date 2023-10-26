dotnet ef migrations add InitialCreate
dotnet ef database update
export ASPNETCORE_ENVIRONMENT=Development
dotnet run --environment="Development"
