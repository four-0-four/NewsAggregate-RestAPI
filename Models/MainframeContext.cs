using Microsoft.EntityFrameworkCore;

namespace mainframe.Models
{
    public class MainframeContext : DbContext
    {
        public MainframeContext(DbContextOptions<MainframeContext> options) : base(options) { }

        public DbSet<EmailSubscription> EmailSubscriptions { get; set; }
    }
}
