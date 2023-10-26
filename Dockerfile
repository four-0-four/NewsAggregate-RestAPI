# Use the official ASP.NET 7 image as the base image
FROM mcr.microsoft.com/dotnet/aspnet:7.0 AS base
WORKDIR /app
EXPOSE 80

# Use the SDK image to build the app
FROM mcr.microsoft.com/dotnet/sdk:7.0 AS build
WORKDIR /src
COPY ["mainframe.csproj", "./"]
RUN dotnet restore "./mainframe.csproj"
COPY . .
WORKDIR "/src/."
RUN dotnet build "mainframe.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "mainframe.csproj" -c Release -o /app/publish

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "mainframe.dll"]
