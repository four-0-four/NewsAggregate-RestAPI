using System.ComponentModel.DataAnnotations;

namespace mainframe.Models
{
    public class EmailSubscription
    {
        [Key]
        public int Id { get; set; }

        [Required]
        [EmailAddress]
        public string Email { get; set; }
    }
}
