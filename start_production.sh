dotnet ef migrations add InitialCreate
dotnet ef database update
export ASPNETCORE_ENVIRONMENT=Production
dotnet run --environment="Production"
