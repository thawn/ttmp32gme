package TTMp32Gme::PrintHandler;

use strict;
use warnings;

use Path::Class;
use Cwd;

use Data::Dumper;

use Log::Message::Simple qw(msg error);

use TTMp32Gme::Build::FileHandler;
use TTMp32Gme::LibraryHandler;
use TTMp32Gme::TttoolHandler;

require Exporter;
our @ISA    = qw(Exporter);
our @EXPORT = qw(create_print_layout);

## internal functions:

sub format_tracks {
	my ( $album, $oid_map, $httpd, $dbh ) = @_;
	my $content;
	my @tracks = sort grep { $_ =~ /^track_/ } keys %{$album};
	foreach my $i ( 0 .. $#tracks ) {
		my @oid = ( $oid_map->{ $album->{ $tracks[$i] }{'tt_script'} }{'code'} );

		#6 mm equals 34.015748031 pixels at 144 dpi
		#(apparently chromium uses 144 dpi on my macbook pro)
		my $oid_file = @{ create_oids( \@oid, 6, $dbh ) }[0];
		my $oid_path = '/assets/images/' . $oid_file->basename();
		put_file_online( $oid_file, $oid_path, $httpd );
		$content .= "<li class='list-group-item'>";
		$content .=
			"<img class='img-6mm track-img' src='$oid_path' alt='oid $oid[0]'>";
		$content .= sprintf(
			"%d. %s<span class='badge'>%02d:%02d</span></li>\n",
			$i + 1,
			$album->{ $tracks[$i] }{'title'},
			$album->{ $tracks[$i] }{'duration'} / 60000,
			$album->{ $tracks[$i] }{'duration'} / 1000 % 60
		);
	}
	return $content;
}

sub format_controls {
	my ( $oid_map, $httpd, $dbh ) = @_;
	my @oids = (
		$oid_map->{'prev'}{'code'}, $oid_map->{'t0'}{'code'},
		$oid_map->{'stop'}{'code'}, $oid_map->{'next'}{'code'}
	);
	my @icons = ( 'backward', 'play', 'stop', 'forward' );
	my $files = create_oids( \@oids, 18, $dbh );
	my $template =
'<a class="btn btn-default play-control"><img class="img-18mm play-img" src="%s" alt="oid: %d">'
		. '<span class="glyphicon glyphicon-%s"></span></a>';
	my $content;
	foreach my $i ( 0 .. $#oids ) {
		my $oid_file = $files->[$i];
		my $oid_path = '/assets/images/' . $oid_file->basename();
		put_file_online( $oid_file, $oid_path, $httpd );
		$content .= sprintf( $template, $oid_path, $oids[$i], $icons[$i] );
	}
	return $content;
}

sub format_main_oid {
	my ( $oid, $oid_map, $httpd, $dbh ) = @_;
	my @oids     = ($oid);
	my $files    = create_oids( \@oids, 18, $dbh );
	my $oid_path = '/assets/images/' . $files->[0]->basename();
	put_file_online( $files->[0], $oid_path, $httpd );
	return
"<img class='img-circle img-18mm play-img' src='$oid_path' alt='oid: $oid'>";
}

## external functions:

sub create_print_layout {
	my ( $oids, $template, $httpd, $dbh ) = @_;
	my $content;
	my $oid_map =
		$dbh->selectall_hashref( "SELECT * FROM script_codes", 'script' );
	my $controls = format_controls( $oid_map, $httpd, $dbh );
	foreach my $oid ( @{$oids} ) {
		if ($oid) {
			my $album = get_album_online( $oid, $httpd, $dbh );
			$album->{'track_list'} = format_tracks( $album, $oid_map, $httpd, $dbh );
			$album->{'play_controls'} = $controls;
			$album->{'main_oid_image'} =
				format_main_oid( $oid, $oid_map, $httpd, $dbh );
			$content .= $template->fill_in( HASH => $album );
		}
	}

	#add general controls:
	$content .= '<div class="row general-controls">';
	$content .= '  <div class="col-xs-6 col-xs-offset-3 general-controls">';
	$content .=
		"<div class=\"btn-group btn-group-lg btn-group-justified\">$controls</div>";
	$content .= '  </div>';

	#todo: add general track controls
	$content .= '</div>';
	return $content;

}

1;
