using Microsoft.AspNetCore.Mvc;
using mainframe.Models;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;


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

            // Check if the email already exists in the database
            var existingSubscription = await _context.EmailSubscriptions
                                                    .FirstOrDefaultAsync(e => e.Email == emailSubscription.Email);
            if (existingSubscription != null)
            {
                return BadRequest("Email is already subscribed.");
            }

            _context.EmailSubscriptions.Add(emailSubscription);
            await _context.SaveChangesAsync();

            return Ok("Subscription successful.");
        }
    }
}
