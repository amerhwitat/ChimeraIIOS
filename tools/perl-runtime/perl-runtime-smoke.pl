use strict;
use warnings;
use Test::More tests => 6;

is(2 + 3, 5, 'arithmetic works');
is(join('-', qw(chimera perl runtime)), 'chimera-perl-runtime', 'lists and join work');
my %runtime = (language => 'Perl', major => 5, minor => 44);
is($runtime{language}, 'Perl', 'hash lookup works');
is("$runtime{major}.$runtime{minor}", '5.44', 'version metadata works');
like("Koronos", qr/^K.*s$/, 'regular expressions work');
my $unicode = "\x{03A9}";
is(length($unicode), 1, 'Unicode string handling works');
