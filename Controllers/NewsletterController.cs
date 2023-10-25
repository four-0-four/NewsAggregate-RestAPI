using Microsoft.AspNetCore.Mvc;
using mainframe.Models;
using System.Threading.Tasks;

namespace mainframe.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class NewsletterController : ControllerBase
    {
        private readonly MainframeContext _context;

        public NewsletterController(MainframeContext context)
        {
            _context = context;
        }

        [HttpPost]
        public async Task<IActionResult> Subscribe([FromBody] EmailSubscription emailSubscription)
        {
            if (emailSubscription == null || string.IsNullOrWhiteSpace(emailSubscription.Email))
            {
                return BadRequest("Invalid email provided.");
            }

            _context.EmailSubscriptions.Add(emailSubscription);
            await _context.SaveChangesAsync();

            return Ok("Subscription successful.");
        }
    }
}
