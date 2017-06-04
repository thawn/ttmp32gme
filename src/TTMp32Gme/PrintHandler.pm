package TTMp32Gme::PrintHandler;

use strict;
use warnings;

use Path::Class;
use Cwd;

use Log::Message::Simple qw(msg debug error);

use TTMp32Gme::Build::FileHandler;
use TTMp32Gme::LibraryHandler;
use TTMp32Gme::TttoolHandler;

require Exporter;
our @ISA    = qw(Exporter);
our @EXPORT = qw(create_print_layout create_pdf format_print_button);

## internal functions:

sub format_tracks {
	my ( $album, $oid_map, $httpd, $dbh ) = @_;
	my $content;
	my @tracks = get_sorted_tracks($album);
	foreach my $i ( 0 .. $#tracks ) {
		my @oid = ( $oid_map->{ $album->{ $tracks[$i] }{'tt_script'} }{'code'} );

		#6 mm equals 34.015748031 pixels at 144 dpi
		#(apparently chromium uses 144 dpi on my macbook pro)
		my $oid_file = @{ create_oids( \@oid, 24, $dbh ) }[0];
		my $oid_path = '/assets/images/' . $oid_file->basename();
		put_file_online( $oid_file, $oid_path, $httpd );
		$content .= "<li class='list-group-item'>";
		$content .=
			"<div class='img-6mm track-img-container'><img class='img-24mm' src='$oid_path' alt='oid $oid[0]'></div>";
		$content .= sprintf(
			"%d. %s (<strong>%02d:%02d</strong>)</li>\n",
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
		$oid_map->{'prev'}{'code'}, $oid_map->{'play'}{'code'},
		$oid_map->{'stop'}{'code'}, $oid_map->{'next'}{'code'}
	);
	my @icons = ( 'backward', 'play', 'stop', 'forward' );
	my $files = create_oids( \@oids, 24, $dbh );
	my $template =
'<a class="btn btn-default play-control"><img class="img-24mm play-img" src="%s" alt="oid: %d">'
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

sub format_track_control {
	my ( $track_no, $oid_map, $httpd, $dbh ) = @_;
	my @oids = ( $oid_map->{ 't' . ( $track_no - 1 ) }{'code'} );
	my $files = create_oids( \@oids, 24, $dbh );
	my $template = '<a class="btn btn-default play-control">'
		. '<img class="img-24mm play-img" src="%s" alt="oid: %d">%d</a>';
	my $oid_path = '/assets/images/' . $files->[0]->basename();
	put_file_online( $files->[0], $oid_path, $httpd );
	return sprintf( $template, $oid_path, $oids[0], $track_no );
}

sub format_main_oid {
	my ( $oid, $oid_map, $httpd, $dbh ) = @_;
	my @oids     = ($oid);
	my $files    = create_oids( \@oids, 24, $dbh );
	my $oid_path = '/assets/images/' . $files->[0]->basename();
	put_file_online( $files->[0], $oid_path, $httpd );
	return
"<img class='img-24mm play-img' src='$oid_path' alt='oid: $oid'>";
}

## external functions:

sub create_print_layout {
	my ( $oids, $template, $config, $httpd, $dbh ) = @_;
	my $content;
	my $oid_map =
		$dbh->selectall_hashref( "SELECT * FROM script_codes", 'script' );
	my $controls = format_controls( $oid_map, $httpd, $dbh );
	foreach my $oid ( @{$oids} ) {
		if ($oid) {
			my $album = get_album_online( $oid, $httpd, $dbh );
			if ( !$album->{'gme_file'} ) {
				$album =
					get_album_online( make_gme( $oid, $config, $dbh ), $httpd, $dbh );
				$oid_map =
					$dbh->selectall_hashref( "SELECT * FROM script_codes", 'script' );
				
			}
			$album->{'track_list'} = format_tracks( $album, $oid_map, $httpd, $dbh );
			$album->{'play_controls'} = $controls;
			$album->{'main_oid_image'} =
				format_main_oid( $oid, $oid_map, $httpd, $dbh );
			$content .= $template->fill_in( HASH => $album );
		}
	}

	#add general controls:
	$content .= '<div id="general-controls" class="row general-controls">';
	$content .=
'  <div class="col-xs-6 col-xs-offset-3 general-controls" style="margin-bottom:10px;">';
	$content .=
		"<div class=\"btn-group btn-group-lg btn-group-justified\">$controls</div>";
	$content .= '  </div>';

	#add general track controls
	$content .= '<div class="col-xs-12" style="margin-bottom:10px;">';
	$content .= '<div class="btn-group btn-group-lg btn-group-justified">';
	my $counter = 1;
	while ( $counter <= $config->{'print_max_track_controls'} ) {
		$content .= format_track_control( $counter, $oid_map, $httpd, $dbh );
		if ( ( $counter < $config->{'print_max_track_controls'} )
			&& ( ( $counter % 12 ) == 0 ) )
		{
			$content .= '</div></div>';
			$content .= '<div class="col-xs-12" style="margin-bottom:10px;">';
			$content .= '<div class="btn-group btn-group-lg btn-group-justified">';
		}
		$counter++;
	}
	$content .= '</div></div></div>';
	return $content;

}

sub create_pdf {
	my ($port) = @_;
	my $wkhtmltopdf_command = get_executable_path('wkhtmltopdf');
	if ($wkhtmltopdf_command) {
		my $pdf_file = file(getLibraryPath(), 'print.pdf');
		my $args = "-B 0.5in -T 0.5in -L 0.5in -R 0.5in http://localhost:$port/pdf $pdf_file";
		my $fullCmd = "$wkhtmltopdf_command $args";
		print "$fullCmd\n";
		if ( $^O =~ /MSWin/ ) {
			my $child_pid;
			my $child_proc;
			require Win32::Process;
  	  Win32::Process::Create($child_proc, $wkhtmltopdf_command, $fullCmd, 0, 0, ".") || error "Could not spawn child: $!";
    	$child_pid = $child_proc->GetProcessID();
		} else {
			$fullCmd .= ' &';
			system($fullCmd);
		}
		return $pdf_file;
	} else {
		error("Could not create pdf, wkhtml2pdf not found.");
		return 0; 
	}
}

sub format_print_button {
	my $button;
	if ( $^O =~ /MSWin/ ) {
		$button = '<button type="button" id="pdf-save" class="btn btn-primary" data-toggle="popover" title="Save as pdf. The PDF usually prints better than the webpage.">Save as PDF</button>';
	} else {
		my $wkhtmltopdf_command = get_executable_path('wkhtmltopdf');
		if ($wkhtmltopdf_command) {
			my $wkhtmltopdf_version = `$wkhtmltopdf_command -V`;
			if ( $wkhtmltopdf_version =~ /0\.13\./ ) {
				$button = '<button type="button" class="btn btn-info" onclick="javascript:window.print()">Print This Page</button> <button type="button" id="pdf-save" class="btn btn-primary" data-toggle="popover" title="Save as pdf. The PDF usually prints better than the webpage.">Save as PDF</button>';
			}	else {
				$button = '<button type="button" class="btn btn-info" onclick="javascript:window.print()">Print This Page</button>';
			}
		} else {
			$button = '<button type="button" class="btn btn-info" onclick="javascript:window.print()">Print This Page</button>';
		}
	}
	return $button;
}

1;
