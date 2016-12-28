package TTMp32Gme::PrintHandler;

use strict;
use warnings;

use Path::Class;
use Cwd;

use Data::Dumper;

use Log::Message::Simple qw(msg error);

use TTMp32Gme::Build::FileHandler;
use TTMp32Gme::LibraryHandler;

require Exporter;
our @ISA    = qw(Exporter);
our @EXPORT = qw(create_print_layout);

## internal functions:

sub format_tracks {
	my ($album) = @_;
	my $content;
	my @tracks = sort grep { $_ =~ /^track_/ } keys %{$album};
	foreach my $i ( 0 .. $#tracks ) {
		$content.=sprintf("<li class='list-group-item'>%d. %s<span class='badge'>%02d:%02d</span></li>\n",$i+1, $album->{$tracks[$i]}{'title'},$album->{$tracks[$i]}{'duration'}/60000, $album->{$tracks[$i]}{'duration'}/1000%60);
	}
	return $content
}

## external functions:

sub create_print_layout {
	my ( $oids, $template, $httpd, $dbh ) = @_;
	my $content;
	foreach my $oid ( @{$oids} ) {
		my $album = get_album_online( $oid, $httpd, $dbh );
		$album->{'track_list'} = format_tracks($album);
			$content .= $template->fill_in( HASH => $album );
			#todo: add album controls
	}
	#todo: add general controls
	return $content;

}

1;
