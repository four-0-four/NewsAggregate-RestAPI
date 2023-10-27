using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using Microsoft.AspNetCore.Hosting;
using Microsoft.EntityFrameworkCore;


namespace mainframe.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class AdminController : ControllerBase
    {
        private readonly IConfiguration _config;
        private readonly IWebHostEnvironment _env;

        public AdminController(IConfiguration config, IWebHostEnvironment env)
        {
            _config = config;
            _env = env;
        }

        [HttpGet("environment")]
        public IActionResult GetEnvironment()
        {
            return Ok(_env.EnvironmentName);
        }

        [HttpGet("hi")]
        public IActionResult GetEnvironment()
        {
            return Ok("hi");
        }

        [HttpGet("connectionstring")]
        public IActionResult GetConnectionString()
        {
            return Ok(_config.GetConnectionString("DefaultConnection"));
        }
    }
}
